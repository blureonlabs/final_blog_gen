"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle, Zap, Globe, ImageIcon, Crown, CheckCircle } from "lucide-react"
import type { UserData } from "@/lib/supabase-api"

interface UsageLimitsProps {
  onUpgrade: () => void
  currentPlan: string
  usage: UserData["usage"]
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

export function UsageLimits({ onUpgrade, currentPlan, usage, userFeatures }: UsageLimitsProps) {
  const isNearLimit = (used: number, limit: number) => used / limit >= 0.8
  const isAtLimit = (used: number, limit: number) => used >= limit
  const isInternalUser = userFeatures?.pricing_tier === 'internal'

  // Use database limits if available, otherwise fall back to props
  const limits = userFeatures?.feature_limits || usage
  const features = userFeatures?.features_enabled

  const imageUsage = {
    used: Math.floor(usage.blogs_generated * 1.5), // Estimate 1.5 images per blog
    limit: limits.images_limit || 50,
  }

  // Don't show usage limits for internal users with unlimited access
  if (isInternalUser) {
    return (
      <Card className="border-green-200 bg-green-50">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Crown className="h-4 w-4 text-green-600" />
              <CardTitle className="text-base text-green-900">Internal Team Access</CardTitle>
            </div>
            <Badge variant="outline" className="border-green-300 text-green-700 text-xs">
              Internal Plan
            </Badge>
          </div>
          <CardDescription className="text-green-700 text-sm">
            You have unlimited access to all features as an internal team member.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-3 px-4 pb-4">
          {/* Blog Generation - Unlimited */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium text-green-900">Blog Generation</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-green-700">
                  {usage.blogs_generated} blogs generated
                </span>
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-xs text-green-600 font-medium">Unlimited</span>
              </div>
            </div>
          </div>

          {/* WordPress Accounts - Unlimited */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium text-green-900">WordPress Accounts</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-green-700">
                  {usage.wordpress_accounts_used} accounts used
                </span>
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-xs text-green-600 font-medium">Unlimited</span>
              </div>
            </div>
          </div>

          {/* AI Image Generation - Unlimited */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ImageIcon className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium text-green-900">AI Image Generation</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-green-700">
                  {imageUsage.used} images generated
                </span>
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-xs text-green-600 font-medium">Unlimited</span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-green-200">
            <div className="text-center text-sm text-green-700">
              <p className="font-medium">✓ All features enabled</p>
              <p className="text-xs">✓ Advanced capabilities unlocked</p>
              <p className="text-xs">✓ Unlimited usage for internal team</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Show regular usage limits for external users
  return (
          <Card className="border-orange-200 bg-orange-50">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-orange-600" />
              <CardTitle className="text-base text-orange-900">Usage Limits</CardTitle>
            </div>
            <Badge variant="outline" className="border-orange-300 text-orange-700 text-xs">
              {currentPlan.charAt(0).toUpperCase() + currentPlan.slice(1)} Plan
            </Badge>
          </div>
          <CardDescription className="text-orange-700 text-sm">
            You're on the free plan with limited features. Upgrade to unlock more capabilities.
          </CardDescription>
        </CardHeader>

      <CardContent className="space-y-4">
        {/* Blog Generation Limit */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-orange-600" />
              <span className="text-sm font-medium text-orange-900">Blog Generation</span>
            </div>
            <span className="text-sm text-orange-700">
              {usage.blogs_generated}/{limits.blogs_limit} blogs
            </span>
          </div>
          <Progress value={(usage.blogs_generated / limits.blogs_limit) * 100} className="h-2" />
          {isAtLimit(usage.blogs_generated, limits.blogs_limit) && (
            <p className="text-xs text-red-600 font-medium">⚠️ Blog limit reached! Upgrade to generate more blogs.</p>
          )}
          {isNearLimit(usage.blogs_generated, limits.blogs_limit) &&
            !isAtLimit(usage.blogs_generated, limits.blogs_limit) && (
              <p className="text-xs text-orange-600">You're close to your blog limit. Consider upgrading soon.</p>
            )}
        </div>

        {/* WordPress Accounts Limit */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-orange-600" />
              <span className="text-sm font-medium text-orange-900">WordPress Accounts</span>
            </div>
            <span className="text-sm text-orange-700">
              {usage.wordpress_accounts_used}/{limits.wordpress_accounts_limit} accounts
            </span>
          </div>
          <Progress value={(usage.wordpress_accounts_used / limits.wordpress_accounts_limit) * 100} className="h-2" />
          <p className="text-xs text-orange-600">
            Free plan allows only 1 WordPress account. Upgrade for multiple sites.
          </p>
        </div>

        {/* Image Generation */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ImageIcon className="h-4 w-4 text-orange-600" />
              <span className="text-sm font-medium text-orange-900">AI Image Generation</span>
            </div>
            <span className="text-sm text-orange-700">
              {imageUsage.used}/{imageUsage.limit} images
            </span>
          </div>
          <Progress value={(imageUsage.used / imageUsage.limit) * 100} className="h-2" />
        </div>

        <div className="pt-3 border-t border-orange-200">
          <Button onClick={onUpgrade} className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-sm py-2">
            Upgrade Now - Starting at ₹499/month
          </Button>
          <div className="mt-2 text-center text-xs text-orange-600">
            <p>✓ Unlimited blogs ✓ Multiple WordPress accounts ✓ Advanced features</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
