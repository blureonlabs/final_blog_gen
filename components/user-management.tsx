"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { supabase } from "@/lib/supabase"
import { User, Search, Filter, RefreshCw, Shield, Crown, UserCheck, UserX, Zap, Globe, ImageIcon, Settings, Star } from "lucide-react"

interface UserData {
  id: string
  email: string
  full_name: string | null
  role: "user" | "admin" | "moderator"
  is_active: boolean
  subscription_plan: string
  created_at: string
  last_login: string | null
  api_usage_current: number
  api_usage_limit: number
  features_enabled?: {
    blog_generation: boolean
    wordpress_accounts: boolean
    ai_image_generation: boolean
    advanced_features: boolean
  }
  feature_limits?: {
    blogs_limit: number
    wordpress_accounts_limit: number
    images_limit: number
  }
  pricing_tier?: string
}

export function UserManagement() {
  const [users, setUsers] = useState<UserData[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [roleFilter, setRoleFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState("all")
  const [tierFilter, setTierFilter] = useState("all")
  const [editingUser, setEditingUser] = useState<string | null>(null)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    setLoading(true)
    try {
      const { data, error } = await supabase
        .from('users')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) {
        console.error("Error loading users:", error)
        return
      }

      setUsers(data || [])
    } catch (error) {
      console.error("Error loading users:", error)
    } finally {
      setLoading(false)
    }
  }

  const updateUserRole = async (userId: string, newRole: string) => {
    try {
      const { error } = await supabase
        .from('users')
        .update({ role: newRole })
        .eq('id', userId)

      if (error) {
        console.error("Error updating user role:", error)
        return
      }

      // Update local state
      setUsers(users.map(user => 
        user.id === userId ? { ...user, role: newRole as any } : user
      ))
    } catch (error) {
      console.error("Error updating user role:", error)
    }
  }

  const toggleUserStatus = async (userId: string, currentStatus: boolean) => {
    try {
      const { error } = await supabase
        .from('users')
        .update({ is_active: !currentStatus })
        .eq('id', userId)

      if (error) {
        console.error("Error updating user status:", error)
        return
      }

      // Update local state
      setUsers(users.map(user => 
        user.id === userId ? { ...user, is_active: !currentStatus } : user
      ))
    } catch (error) {
      console.error("Error updating user status:", error)
    }
  }

  const updateUserFeatures = async (userId: string, features: any, limits: any, tier: string) => {
    try {
      const { error } = await supabase
        .from('users')
        .update({ 
          features_enabled: features,
          feature_limits: limits,
          pricing_tier: tier
        })
        .eq('id', userId)

      if (error) {
        console.error("Error updating user features:", error)
        return
      }

      // Update local state
      setUsers(users.map(user => 
        user.id === userId ? { 
          ...user, 
          features_enabled: features,
          feature_limits: limits,
          pricing_tier: tier
        } : user
      ))

      setEditingUser(null)
    } catch (error) {
      console.error("Error updating user features:", error)
    }
  }

  const makeUserInternal = async (userId: string) => {
    const internalFeatures = {
      blog_generation: true,
      wordpress_accounts: true,
      ai_image_generation: true,
      advanced_features: true
    }

    const internalLimits = {
      blogs_limit: 999999,
      wordpress_accounts_limit: 999,
      images_limit: 9999
    }

    await updateUserFeatures(userId, internalFeatures, internalLimits, 'internal')
  }

  const makeUserExternal = async (userId: string) => {
    const externalFeatures = {
      blog_generation: true,
      wordpress_accounts: false,
      ai_image_generation: false,
      advanced_features: false
    }

    const externalLimits = {
      blogs_limit: 10,
      wordpress_accounts_limit: 1,
      images_limit: 50
    }

    await updateUserFeatures(userId, externalFeatures, externalLimits, 'free')
  }

  const getRoleIcon = (role: string) => {
    switch (role) {
      case "admin":
        return <Crown className="w-4 h-4 text-yellow-600" />
      case "moderator":
        return <Shield className="w-4 h-4 text-blue-600" />
      default:
        return <User className="w-4 h-4 text-gray-600" />
    }
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case "admin":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "moderator":
        return "bg-blue-100 text-blue-800 border-blue-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getStatusColor = (status: boolean) => {
    return status ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
  }

  const getTierColor = (tier: string) => {
    switch (tier) {
      case "internal":
        return "bg-purple-100 text-purple-800 border-purple-200"
      case "enterprise":
        return "bg-indigo-100 text-indigo-800 border-indigo-200"
      case "pro":
        return "bg-blue-100 text-blue-800 border-blue-200"
      case "basic":
        return "bg-green-100 text-green-800 border-green-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      searchTerm === "" ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.full_name && user.full_name.toLowerCase().includes(searchTerm.toLowerCase()))

    const matchesRole = roleFilter === "all" || user.role === roleFilter
    const matchesStatus = statusFilter === "all" || 
      (statusFilter === "active" && user.is_active) ||
      (statusFilter === "inactive" && !user.is_active)
    const matchesTier = tierFilter === "all" || user.pricing_tier === tierFilter

    return matchesSearch && matchesRole && matchesStatus && matchesTier
  })

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded mb-6"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                User Management
              </CardTitle>
              <CardDescription>
                Manage user accounts, roles, permissions, and feature access
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={loadUsers}
              disabled={loading}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Search users by email or name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={roleFilter} onValueChange={setRoleFilter}>
              <SelectTrigger className="w-full md:w-40">
                <SelectValue placeholder="Filter by role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="user">Users</SelectItem>
                <SelectItem value="moderator">Moderators</SelectItem>
                <SelectItem value="admin">Admins</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full md:w-40">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
            <Select value={tierFilter} onValueChange={setTierFilter}>
              <SelectTrigger className="w-full md:w-40">
                <SelectValue placeholder="Filter by tier" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tiers</SelectItem>
                <SelectItem value="internal">Internal</SelectItem>
                <SelectItem value="enterprise">Enterprise</SelectItem>
                <SelectItem value="pro">Pro</SelectItem>
                <SelectItem value="basic">Basic</SelectItem>
                <SelectItem value="free">Free</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Users List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Users ({filteredUsers.length})</CardTitle>
          <CardDescription>
            Manage user accounts, permissions, and feature access
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredUsers.length === 0 ? (
            <div className="text-center py-8">
              <User className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No users found matching your filters</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredUsers.map((user) => (
                <div
                  key={user.id}
                  className="border rounded-lg overflow-hidden"
                >
                  {/* User Header */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 border-b">
                    <div className="flex items-center gap-4">
                      <div className="flex-shrink-0">
                        {getRoleIcon(user.role)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium">{user.full_name || 'No Name'}</h4>
                          <Badge className={`text-xs border ${getRoleColor(user.role)}`}>
                            {user.role.toUpperCase()}
                          </Badge>
                          <Badge className={`text-xs ${getStatusColor(user.is_active)}`}>
                            {user.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                          {user.pricing_tier && (
                            <Badge className={`text-xs border ${getTierColor(user.pricing_tier)}`}>
                              {user.pricing_tier.toUpperCase()}
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">{user.email}</p>
                        <p className="text-xs text-gray-500">
                          Created: {new Date(user.created_at).toLocaleDateString()}
                          {user.last_login && ` • Last login: ${new Date(user.last_login).toLocaleDateString()}`}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Role Update */}
                      <Select
                        value={user.role}
                        onValueChange={(newRole) => updateUserRole(user.id, newRole)}
                      >
                        <SelectTrigger className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="user">User</SelectItem>
                          <SelectItem value="moderator">Moderator</SelectItem>
                          <SelectItem value="admin">Admin</SelectItem>
                        </SelectContent>
                      </Select>

                      {/* Status Toggle */}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => toggleUserStatus(user.id, user.is_active)}
                        className={user.is_active ? "text-red-600 hover:text-red-700" : "text-green-600 hover:text-green-700"}
                      >
                        {user.is_active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                      </Button>

                      {/* Quick Actions */}
                      <div className="flex gap-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => makeUserInternal(user.id)}
                          className="text-purple-600 hover:text-purple-700"
                          title="Make Internal Member"
                        >
                          <Star className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => makeUserExternal(user.id)}
                          className="text-gray-600 hover:text-gray-700"
                          title="Make External User"
                        >
                          <User className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setEditingUser(editingUser === user.id ? null : user.id)}
                          className="text-blue-600 hover:text-blue-700"
                          title="Edit Features"
                        >
                          <Settings className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Feature Editor */}
                  {editingUser === user.id && (
                    <div className="p-4 bg-blue-50 border-b">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Features Enabled */}
                        <div className="space-y-3">
                          <h5 className="font-medium text-sm text-gray-700">Features Enabled</h5>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <Label className="text-xs flex items-center gap-2">
                                <Zap className="w-3 h-3" />
                                Blog Generation
                              </Label>
                              <Switch
                                checked={user.features_enabled?.blog_generation || false}
                                onCheckedChange={(checked) => {
                                  const newFeatures = {
                                    ...user.features_enabled,
                                    blog_generation: checked
                                  }
                                  setUsers(users.map(u => 
                                    u.id === user.id ? { ...u, features_enabled: newFeatures } : u
                                  ))
                                }}
                              />
                            </div>
                            <div className="flex items-center justify-between">
                              <Label className="text-xs flex items-center gap-2">
                                <Globe className="w-3 h-3" />
                                WordPress Accounts
                              </Label>
                              <Switch
                                checked={user.features_enabled?.wordpress_accounts || false}
                                onCheckedChange={(checked) => {
                                  const newFeatures = {
                                    ...user.features_enabled,
                                    wordpress_accounts: checked
                                  }
                                  setUsers(users.map(u => 
                                    u.id === user.id ? { ...u, features_enabled: newFeatures } : u
                                  ))
                                }}
                              />
                            </div>
                            <div className="flex items-center justify-between">
                              <Label className="text-xs flex items-center gap-2">
                                <ImageIcon className="w-3 h-3" />
                                AI Image Generation
                              </Label>
                              <Switch
                                checked={user.features_enabled?.ai_image_generation || false}
                                onCheckedChange={(checked) => {
                                  const newFeatures = {
                                    ...user.features_enabled,
                                    ai_image_generation: checked
                                  }
                                  setUsers(users.map(u => 
                                    u.id === user.id ? { ...u, features_enabled: newFeatures } : u
                                  ))
                                }}
                              />
                            </div>
                            <div className="flex items-center justify-between">
                              <Label className="text-xs flex items-center gap-2">
                                <Settings className="w-3 h-3" />
                                Advanced Features
                              </Label>
                              <Switch
                                checked={user.features_enabled?.advanced_features || false}
                                onCheckedChange={(checked) => {
                                  const newFeatures = {
                                    ...user.features_enabled,
                                    advanced_features: checked
                                  }
                                  setUsers(users.map(u => 
                                    u.id === user.id ? { ...u, features_enabled: newFeatures } : u
                                  ))
                                }}
                              />
                            </div>
                          </div>
                        </div>

                        {/* Feature Limits */}
                        <div className="space-y-3">
                          <h5 className="font-medium text-sm text-gray-700">Feature Limits</h5>
                          <div className="space-y-2">
                            <div>
                              <Label className="text-xs">Blogs Limit</Label>
                              <Input
                                type="number"
                                value={user.feature_limits?.blogs_limit || 0}
                                onChange={(e) => {
                                  const newLimits = {
                                    ...user.feature_limits,
                                    blogs_limit: parseInt(e.target.value) || 0
                                  }
                                  setUsers(users.map(u => 
                                    u.id === user.id ? { ...u, feature_limits: newLimits } : u
                                  ))
                                }}
                                className="h-8 text-xs"
                              />
                            </div>
                            <div>
                              <Label className="text-xs">WordPress Accounts Limit</Label>
                              <Input
                                type="number"
                                value={user.feature_limits?.wordpress_accounts_limit || 0}
                                onChange={(e) => {
                                  const newLimits = {
                                    ...user.feature_limits,
                                    wordpress_accounts_limit: parseInt(e.target.value) || 0
                                  }
                                  setUsers(users.map(u => 
                                    u.id === user.id ? { ...u, feature_limits: newLimits } : u
                                  ))
                                }}
                                className="h-8 text-xs"
                              />
                            </div>
                            <div>
                              <Label className="text-xs">Images Limit</Label>
                              <Input
                                type="number"
                                value={user.feature_limits?.images_limit || 0}
                                onChange={(e) => {
                                  const newLimits = {
                                    ...user.feature_limits,
                                    images_limit: parseInt(e.target.value) || 0
                                  }
                                  setUsers(users.map(u => 
                                    u.id === user.id ? { ...u, feature_limits: newLimits } : u
                                  ))
                                }}
                                className="h-8 text-xs"
                              />
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Save/Cancel Buttons */}
                      <div className="flex gap-2 mt-4 pt-3 border-t">
                        <Button
                          size="sm"
                          onClick={() => updateUserFeatures(
                            user.id,
                            user.features_enabled,
                            user.feature_limits,
                            user.pricing_tier || 'free'
                          )}
                        >
                          Save Changes
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setEditingUser(null)}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* Usage Info */}
                  <div className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">API Usage:</span>
                        <span className="ml-2 font-medium">
                          {user.api_usage_current}/{user.api_usage_limit}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Plan:</span>
                        <span className="ml-2 font-medium">{user.subscription_plan}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Tier:</span>
                        <span className="ml-2 font-medium">{user.pricing_tier || 'free'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
