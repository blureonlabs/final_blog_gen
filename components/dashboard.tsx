"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { ProjectList } from "@/components/project-list"
import { NewProjectModal } from "@/components/new-project-modal"
import { ProjectDetail } from "@/components/project-detail"
import { Settings } from "@/components/settings"
import { Logs } from "@/components/logs"
import { AdminPanel } from "@/components/admin-panel"

import { Plus, LogOut, User as UserIcon, Settings as SettingsIcon, Shield, RefreshCw } from "lucide-react"

import { Pricing } from "@/components/pricing"
import { supabaseApi, type UserData as SupabaseUserData, type Project } from "@/lib/supabase-api"
import { authManager, type User } from "@/lib/auth"
import { ProfileSettings } from "@/components/profile-settings"
import { usePermissions } from "@/lib/use-permissions"
import { UserManagement } from "@/components/user-management"
import { supabaseLogger } from "@/lib/supabase-logging"

interface DashboardProps {
  user: User
}

export function Dashboard({ user }: DashboardProps) {
  const [activeView, setActiveView] = useState<"dashboard" | "projects" | "project" | "settings" | "logs" | "admin">("dashboard")
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [showNewProject, setShowNewProject] = useState(false)
  const [showPricing, setShowPricing] = useState(false)
  const [showProfileSettings, setShowProfileSettings] = useState(false) // Added state
  const [userData, setUserData] = useState<SupabaseUserData | null>(null)
  const [loading, setLoading] = useState(true)
  const permissions = usePermissions()

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await supabaseApi.getUserData()
        setUserData(data)
      } catch (error) {
        console.error("Error loading user data:", error)
        setUserData(null) // Fallback to default data
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  const handleSignOut = async () => {
    try {
      await authManager.signOut()
      // The auth system will handle the redirect
    } catch (error) {
      console.error("Sign out failed:", error)
    }
  }

  const handleProjectSelect = (projectId: string) => {
    setSelectedProjectId(projectId)
    setActiveView("project")
    // No need to log every project view
  }

  const handleProjectCreated = async (newProject: Project) => {
    if (userData) {
      const updatedData = { ...userData, projects: [...userData.projects, newProject] }
      setUserData(updatedData)
      // Log project creation - this is a major event
      supabaseLogger.info("generation", "User created new project", { 
        project_name: newProject.name,
        project_id: newProject.id 
      })
    }
    setShowNewProject(false)
  }

  const handleDataUpdate = async () => {
    const updatedData = await supabaseApi.getUserData()
    setUserData(updatedData)
    // No need to log data refresh
  }

  // Add logging for view changes
  const handleViewChange = (view: "dashboard" | "projects" | "project" | "settings" | "logs" | "admin") => {
    setActiveView(view)
    // Only log admin access for security tracking
    if (view === "admin" && permissions.isAdmin) {
      supabaseLogger.info("user", "Admin accessed admin panel")
    }
  }

  if (loading || !userData) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading your dashboard...</p>
        </div>
      </div>
    )
  }

  const activeProjects = userData.projects.filter((project) => project.status !== "completed")
  const completedProjects = userData.projects.filter((project) => project.status === "completed")

  return (
    <div className="min-h-screen bg-background">
      <header className="bg-card shadow-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <h1 className="text-2xl font-bold text-foreground">Bulk Blog Generator</h1>
              <nav className="flex space-x-1">
                <button
                  onClick={() => handleViewChange("dashboard")}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeView === "dashboard"
                      ? "bg-accent text-accent-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  }`}
                >
                  Dashboard
                </button>
                <button
                  onClick={() => handleViewChange("projects")}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeView === "projects"
                      ? "bg-accent text-accent-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  }`}
                >
                  Projects
                </button>
                {permissions.canViewAdmin && (
                  <button
                    onClick={() => setActiveView("admin")}
                    className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                      activeView === "admin"
                        ? "bg-accent text-accent-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    }`}
                  >
                    Admin
                  </button>
                )}
                <button
                  onClick={() => setActiveView("logs")}
                  className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeView === "logs"
                      ? "bg-accent text-accent-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  }`}
                >
                  Logs
                </button>

              </nav>
            </div>
            <div className="flex items-center gap-4">
              {/* Settings Button */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setActiveView("settings")}
                className="flex items-center gap-2 hover:bg-accent hover:text-accent-foreground"
                title="Application Settings"
              >
                <SettingsIcon className="w-4 h-4" />
              </Button>
              
              {/* Refresh Profile Button (Admin only) */}
              {permissions.isAdmin && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={async () => {
                    try {
                      await authManager.refreshUserProfile()
                      // Force a page refresh to update the UI
                      window.location.reload()
                    } catch (error) {
                      console.error('Failed to refresh profile:', error)
                    }
                  }}
                  className="flex items-center gap-2 hover:bg-accent hover:text-accent-foreground"
                  title="Refresh Profile Data (Admin)"
                >
                  <RefreshCw className="w-4 h-4" />
                  Refresh Profile
                </Button>
              )}
              
              {/* Profile Button */}
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowProfileSettings(true)}
                disabled={!userData}
                className="flex items-center gap-2 hover:bg-accent hover:text-accent-foreground disabled:opacity-50 disabled:cursor-not-allowed"
                title={userData ? `${user.full_name || user.email} - Click to edit profile` : "Loading profile data..."}
              >
                <UserIcon className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {activeView === "dashboard" && (
          <div>
            <div className="flex justify-between items-start mb-12">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold text-foreground">Your Projects</h2>
                <p className="text-lg text-muted-foreground">
                  {userData.projects.length === 0
                    ? "Create your first blog generation project"
                    : "Manage your bulk blog generation projects"}
                </p>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>Role: {permissions.role}</span>
                  {permissions.isAdmin && <span className="text-yellow-600">• Admin Access</span>}
                  {permissions.isModerator && <span className="text-blue-600">• Moderator Access</span>}
                </div>
              </div>
              {permissions.canCreateProjects && (
                <Button
                  onClick={() => setShowNewProject(true)}
                  className="bg-accent hover:bg-accent/90 text-accent-foreground shadow-sm px-6 py-2.5 rounded-lg font-medium"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  New Project
                </Button>
              )}
            </div>

            {userData.projects.length === 0 ? (
              <div className="text-center py-16">
                <div className="bg-muted/50 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <Plus className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-2">No projects yet</h3>
                <p className="text-muted-foreground mb-6">Get started by creating your first blog generation project</p>
                <Button
                  onClick={() => setShowNewProject(true)}
                  className="bg-accent hover:bg-accent/90 text-accent-foreground"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Project
                </Button>
              </div>
            ) : (
              <>
                {activeProjects.length > 0 && (
                  <div className="mb-12">
                    <h3 className="text-xl font-semibold text-foreground mb-6">Active Projects</h3>
                    <ProjectList projects={activeProjects} loading={false} onProjectSelect={handleProjectSelect} />
                  </div>
                )}

                {completedProjects.length > 0 && (
                  <div>
                    <h3 className="text-xl font-semibold text-foreground mb-6">Completed Projects</h3>
                    <ProjectList projects={completedProjects} loading={false} onProjectSelect={handleProjectSelect} />
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeView === "project" && selectedProjectId && (
          <ProjectDetail
            projectId={selectedProjectId}
            onBack={() => setActiveView("dashboard")}
            onUpdate={handleDataUpdate}
          />
        )}

        {activeView === "projects" && (
          <div>
            <div className="flex justify-between items-start mb-8">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold text-foreground">All Projects</h2>
                <p className="text-lg text-muted-foreground">
                  {userData.projects.length === 0
                    ? "Create your first blog generation project"
                    : "View and manage all your blog generation projects"}
                </p>
              </div>
              {permissions.canCreateProjects && (
                <Button
                  onClick={() => setShowNewProject(true)}
                  className="bg-accent hover:bg-accent/90 text-accent-foreground shadow-sm px-6 py-2.5 rounded-lg font-medium"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  New Project
                </Button>
              )}
            </div>

            {userData.projects.length === 0 ? (
              <div className="text-center py-16">
                <div className="bg-muted/50 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <Plus className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-2">No projects yet</h3>
                <p className="text-muted-foreground mb-6">Get started by creating your first blog generation project</p>
                <Button
                  onClick={() => setShowNewProject(true)}
                  className="bg-accent hover:bg-accent/90 text-accent-foreground"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Project
                </Button>
              </div>
            ) : (
              <div className="space-y-8">
                {activeProjects.length > 0 && (
                  <div>
                    <h3 className="text-xl font-semibold text-foreground mb-6">Active Projects ({activeProjects.length})</h3>
                    <ProjectList projects={activeProjects} loading={false} onProjectSelect={handleProjectSelect} />
                  </div>
                )}

                {completedProjects.length > 0 && (
                  <div>
                    <h3 className="text-xl font-semibold text-foreground mb-6">Completed Projects ({completedProjects.length})</h3>
                    <ProjectList projects={completedProjects} loading={false} onProjectSelect={handleProjectSelect} />
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {activeView === "admin" && (
          <div>
            {permissions.canManageUsers ? (
              <AdminPanel />
            ) : (
              <div className="text-center py-16">
                <div className="bg-muted/50 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <Shield className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-2">Access Denied</h3>
                <p className="text-muted-foreground mb-6">You don't have permission to access the admin panel.</p>
              </div>
            )}
          </div>
        )}

        {activeView === "settings" && <Settings onUpdate={handleDataUpdate} />}

        {activeView === "logs" && <Logs />}


      </main>

      {showNewProject && (
        <NewProjectModal
          onClose={() => setShowNewProject(false)}
          onSuccess={handleProjectCreated}
          userId={user.id}
          userData={userData}
        />
      )}

      {showPricing && (
        <Pricing
          onClose={() => setShowPricing(false)}
          currentPlan={userData.subscription.plan}
          onUpgrade={handleDataUpdate}
        />
      )}

      {/* Profile Settings Modal */}
      {showProfileSettings && (
        <ProfileSettings
          user={user}
          onClose={() => setShowProfileSettings(false)}
          userData={userData}
        />
      )}
    </div>
  )
}
