"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Users, Shield, Settings, Crown, Activity, Database } from "lucide-react"
import { UserManagement } from "@/components/user-management"
import { DatabaseHealth } from "@/components/database-health"

export function AdminPanel() {
  const [activeTab, setActiveTab] = useState<"users" | "health">("users")

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="space-y-2">
          <h2 className="text-3xl font-bold text-foreground">Admin Panel</h2>
          <p className="text-lg text-muted-foreground">Manage users and monitor system health</p>
        </div>
        <div className="flex items-center gap-2">
          <Crown className="h-6 w-6 text-yellow-600" />
          <Badge variant="outline" className="border-yellow-300 text-yellow-700">
            Admin Access
          </Badge>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-1 border-b">
        <button
          onClick={() => setActiveTab("users")}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors flex items-center gap-2 ${
            activeTab === "users"
              ? "bg-accent text-accent-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground hover:bg-muted"
          }`}
        >
          <Users className="w-4 h-4" />
          User Management
        </button>
        <button
          onClick={() => setActiveTab("health")}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors flex items-center gap-2 ${
            activeTab === "health"
              ? "bg-accent text-accent-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground hover:bg-muted"
          }`}
        >
          <Database className="w-4 h-4" />
          System Health
        </button>
      </div>

      {/* Tab Content */}
      <div className="min-h-[600px]">
        {activeTab === "users" && (
          <div>
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  User Management
                </CardTitle>
                <CardDescription>
                  Manage user accounts, roles, permissions, and feature access. 
                  Convert users to internal members for unlimited access.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <Users className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                    <p className="font-medium text-blue-900">User Management</p>
                    <p className="text-xs text-blue-700">Manage roles, permissions, and access</p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <Crown className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                    <p className="font-medium text-purple-900">Internal Access</p>
                    <p className="text-xs text-purple-700">Convert users to internal members</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <Settings className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    <p className="font-medium text-green-900">Feature Control</p>
                    <p className="text-xs text-green-700">Enable/disable features per user</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <UserManagement />
          </div>
        )}

        {activeTab === "health" && (
          <div>
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="w-5 h-5" />
                  System Health
                </CardTitle>
                <CardDescription>
                  Monitor database connectivity, table status, and system performance
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <Database className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    <p className="font-medium text-green-900">Database Status</p>
                    <p className="text-xs text-green-700">Connection and table health</p>
                  </div>
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <Activity className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                    <p className="font-medium text-blue-900">Performance</p>
                    <p className="text-xs text-blue-700">System metrics and monitoring</p>
                  </div>
                  <div className="text-center p-4 bg-orange-50 rounded-lg">
                    <Shield className="h-8 w-8 text-orange-600 mx-auto mb-2" />
                    <p className="font-medium text-orange-900">Security</p>
                    <p className="text-xs text-orange-700">RLS policies and access control</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <DatabaseHealth />
          </div>
        )}
      </div>
    </div>
  )
}
