"use client"

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ProjectList } from "@/components/project-list"
import { NewProjectModal } from "@/components/new-project-modal"
import { ContentGenerationModal } from "@/components/content-generation-modal"
import { ProjectDetail } from "@/components/project-detail"
import { Settings } from "@/components/settings"
import { Logs } from "@/components/logs"
import { AdminPanel } from "@/components/admin-panel"

import { Plus, LogOut, User as UserIcon, Settings as SettingsIcon, Shield, RefreshCw, FileText } from "lucide-react"

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
  const router = useRouter()
  const searchParams = useSearchParams()
  const [activeView, setActiveView] = useState<"dashboard" | "admin" | "settings" | "projects" | "project" | "logs">("dashboard")
  const [showNewProject, setShowNewProject] = useState(false)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const [showContentGenerationModal, setShowContentGenerationModal] = useState(false)
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [showProfileSettings, setShowProfileSettings] = useState(false) // Added state
  const [userData, setUserData] = useState<SupabaseUserData | null>(null)
  const [loading, setLoading] = useState(true)
  const [modalKey, setModalKey] = useState(0)
  const permissions = usePermissions()
  
  // Tab state for Projects view
  const [activeProjectsTab, setActiveProjectsTab] = useState<"active" | "completed" | "failed">("active")

  // Function to open new project modal with fresh state
  const openNewProjectModal = () => {
    console.log("🔄 Opening new project modal, current modalKey:", modalKey)
    setModalKey(prev => {
      const newKey = prev + 1
      console.log("🔄 Incrementing modalKey from", prev, "to", newKey)
      return newKey
    })
    setShowNewProject(true)
    console.log("🔄 Modal should now be visible with key:", modalKey + 1)
  }

  // Initialize view from URL on component mount and URL changes
  useEffect(() => {
    const viewFromUrl = searchParams.get('view') as "dashboard" | "admin" | "settings" | "projects" | "project" | "logs" | null
    const projectIdFromUrl = searchParams.get('projectId')
    
    if (viewFromUrl && viewFromUrl !== activeView) {
      setActiveView(viewFromUrl)
    }
    
    if (projectIdFromUrl && projectIdFromUrl !== selectedProjectId) {
      setSelectedProjectId(projectIdFromUrl)
      // Find the project in userData if available
      if (userData) {
        const project = userData.projects.find(p => p.id === projectIdFromUrl)
        if (project) {
          setSelectedProject(project)
        } else {
          // Project not found, redirect to dashboard
          console.warn(`Project with ID ${projectIdFromUrl} not found, redirecting to dashboard`)
          setActiveView("dashboard")
          setSelectedProjectId(null)
          setSelectedProject(null)
          updateUrl("dashboard")
        }
      }
    }
  }, [searchParams, activeView, selectedProjectId, userData])

  // Set initial view from URL on first load
  useEffect(() => {
    const viewFromUrl = searchParams.get('view') as "dashboard" | "admin" | "settings" | "projects" | "project" | "logs" | null
    if (viewFromUrl) {
      setActiveView(viewFromUrl)
    }
  }, []) // Only run once on mount

  // Handle browser back/forward navigation
  useEffect(() => {
    const handlePopState = () => {
      const viewFromUrl = searchParams.get('view') as "dashboard" | "admin" | "settings" | "projects" | "project" | "logs" | null
      const projectIdFromUrl = searchParams.get('projectId')
      
      if (viewFromUrl) {
        setActiveView(viewFromUrl)
      }
      
      if (projectIdFromUrl) {
        setSelectedProjectId(projectIdFromUrl)
        if (userData) {
          const project = userData.projects.find(p => p.id === projectIdFromUrl)
          if (project) {
            setSelectedProject(project)
          } else {
            // Project not found, redirect to dashboard
            console.warn(`Project with ID ${projectIdFromUrl} not found, redirecting to dashboard`)
            setActiveView("dashboard")
            setSelectedProjectId(null)
            setSelectedProject(null)
            updateUrl("dashboard")
          }
        }
      } else {
        setSelectedProjectId(null)
        setSelectedProject(null)
      }
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [searchParams, userData])

  // Update URL when view changes
  const updateUrl = (view: string, projectId?: string | null) => {
    const params = new URLSearchParams()
    params.set('view', view)
    if (projectId) {
      params.set('projectId', projectId)
    }
    const newUrl = `${window.location.pathname}?${params.toString()}`
    router.replace(newUrl, { scroll: false })
  }

  // Handle direct navigation to project URLs
  const handleDirectProjectNavigation = (projectId: string) => {
    if (userData) {
      const project = userData.projects.find(p => p.id === projectId)
      if (project) {
        setSelectedProject(project)
        setSelectedProjectId(projectId)
        setActiveView("project")
        updateUrl("project", projectId)
        return true
      }
    }
    return false
  }

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await supabaseApi.getUserData()
        console.log("🚀 Initial user data loaded:", data)
        console.log("🔍 Initial projects num_blogs:", data.projects.map(p => ({ id: p.id, name: p.name, num_blogs: p.num_blogs })))
        setUserData(data)
        
        // After loading userData, check if we need to restore project view from URL
        const projectIdFromUrl = searchParams.get('projectId')
        if (projectIdFromUrl) {
          const project = data.projects.find(p => p.id === projectIdFromUrl)
          if (project) {
            setSelectedProject(project)
            setSelectedProjectId(projectIdFromUrl)
            setActiveView("project")
          } else {
            // Project not found, redirect to dashboard
            console.warn(`Project with ID ${projectIdFromUrl} not found, redirecting to dashboard`)
            setActiveView("dashboard")
            setSelectedProjectId(null)
            setSelectedProject(null)
            updateUrl("dashboard")
          }
        }
      } catch (error) {
        console.error("Error loading user data:", error)
        setUserData(null) // Fallback to default data
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [searchParams])

  const handleSignOut = async () => {
    try {
      await authManager.signOut()
      // The auth system will handle the redirect
    } catch (error) {
      console.error("Sign out failed:", error)
    }
  }

  const handleProjectSelect = (projectId: string) => {
    const project = userData?.projects.find(p => p.id === projectId)
    console.log("🔍 Selected project:", project)
    console.log("🔍 Project num_blogs:", project?.num_blogs)
    console.log("🔍 Project ID from parameter:", projectId)
    console.log("🔍 Project ID from object:", project?.id)
    console.log("🔍 All projects in userData:", userData?.projects.map(p => ({ id: p.id, name: p.name, num_blogs: p.num_blogs })))
    if (project) {
      setSelectedProjectId(projectId)
      setSelectedProject(project)
      setActiveView("project")
      updateUrl("project", projectId)
      console.log("🔍 Set selectedProjectId to:", projectId)
      console.log("🔍 Set selectedProject to:", project)
    }
  }

  const handleResume = (project: Project) => {
    setSelectedProject(project)
    setShowContentGenerationModal(true)
  }

  const handleProjectCreated = async (newProject: Project) => {
    console.log("🆕 New project created:", newProject)
    console.log("🔍 New project num_blogs:", newProject.num_blogs)
    
    if (userData) {
      const updatedData = { ...userData, projects: [...userData.projects, newProject] }
      console.log("🔄 Updated userData projects:", updatedData.projects.map(p => ({ id: p.id, name: p.name, num_blogs: p.num_blogs })))
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
    console.log("🔄 Dashboard data updated:", updatedData)
    console.log("🔍 Projects num_blogs:", updatedData.projects.map(p => ({ id: p.id, name: p.name, num_blogs: p.num_blogs })))
    setUserData(updatedData)
    // No need to log data refresh
  }

  // Add logging for view changes
  const handleViewChange = (view: "dashboard" | "projects" | "project" | "settings" | "logs" | "admin") => {
    setActiveView(view)
    updateUrl(view, view === "project" ? selectedProjectId : null)
    
    // Reset projects tab to active when switching to projects view
    if (view === "projects") {
      setActiveProjectsTab("active")
    }
    
    // Only log admin access for security tracking
    if (view === "admin" && permissions.isAdmin) {
      supabaseLogger.info("user", "Admin accessed admin panel")
    }
  }

  // Simple function to get project status - just use what's in the database
  const getProjectStatus = (project: Project): string => {
    return project.status
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

  const activeProjects = userData.projects.filter((project) => {
    // Active projects are those that are in progress, partial, or ready
    return project.status === "in_progress" || project.status === "partial" || project.status === "ready"
  })
  const completedProjects = userData.projects.filter((project) => {
    // Completed projects are only those explicitly marked as completed
    return project.status === "completed"
  })
  const failedProjects = userData.projects.filter((project) => {
    // Failed projects are those with failed status
    return project.status === "failed"
  })

  return (
    <div className="min-h-screen bg-background">
      <header className="bg-card shadow-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <h1 className="text-2xl font-bold text-foreground">Blu Blog Gen</h1>
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
                    onClick={() => handleViewChange("admin")}
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
                  onClick={() => handleViewChange("logs")}
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
                onClick={() => handleViewChange("settings")}
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
                    : "Manage your Blu Blog Gen projects"}
                </p>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>Role: {permissions.role}</span>
                  {permissions.isAdmin && <span className="text-yellow-600">• Admin Access</span>}
                  {permissions.isModerator && <span className="text-blue-600">• Moderator Access</span>}
                </div>
              </div>
              {permissions.canCreateProjects && (
                <Button
                  onClick={openNewProjectModal}
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
                  onClick={openNewProjectModal}
                  className="bg-accent hover:bg-accent/90 text-accent-foreground"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Project
                </Button>
              </div>
            ) : (
              <>
                {/* Project Statistics Overview */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Total Projects</p>
                        <p className="text-2xl font-bold text-foreground">{userData.projects.length}</p>
                      </div>
                      <div className="h-8 w-8 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 dark:text-blue-400 text-sm font-medium">📊</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Active Projects</p>
                        <p className="text-2xl font-bold text-foreground">{activeProjects.length}</p>
                      </div>
                      <div className="h-8 w-8 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center">
                        <span className="text-green-600 dark:text-green-400 text-sm font-medium">🔄</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Completed Projects</p>
                        <p className="text-2xl font-bold text-foreground">{completedProjects.length}</p>
                      </div>
                      <div className="h-8 w-8 bg-emerald-100 dark:bg-emerald-900/20 rounded-full flex items-center justify-center">
                        <span className="text-emerald-600 dark:text-emerald-400 text-sm font-medium">✅</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Failed Projects</p>
                        <p className="text-2xl font-bold text-foreground">{failedProjects.length}</p>
                      </div>
                      <div className="h-8 w-8 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
                        <span className="text-red-600 dark:text-red-400 text-sm font-medium">❌</span>
                      </div>
                    </div>
                  </div>
                </div>

                                 {activeProjects.length > 0 && (
                    <div className="mb-12">
                      <h3 className="text-xl font-semibold text-foreground mb-6">Active Projects</h3>
                      <p className="text-sm text-muted-foreground mb-4">
                        Projects that are in progress, partially generated, or ready to start
                      </p>
                      <ProjectList projects={activeProjects} loading={false} onProjectSelect={handleProjectSelect} onResume={handleResume} />
                    </div>
                  )}
              </>
            )}
          </div>
        )}

        {activeView === "project" && selectedProjectId && selectedProject && (
          <>
            {console.log("🔍 Rendering ProjectDetail with:")}
            {console.log("🔍 selectedProjectId:", selectedProjectId)}
            {console.log("🔍 selectedProject.id:", selectedProject.id)}
            {console.log("🔍 selectedProject:", selectedProject)}
            <ProjectDetail
              projectId={selectedProjectId}
              project={{
                ...selectedProject,
                user_id: user.id // Add the missing user_id field
              } as any}
              onBack={() => {
                setActiveView("dashboard")
                updateUrl("dashboard")
              }}
              onUpdate={handleDataUpdate}
            />
          </>
        )}

        {activeView === "projects" && (
          <div>
            <div className="flex justify-between items-start mb-8">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold text-foreground">All Projects</h2>
                <p className="text-lg text-muted-foreground">
                  {userData.projects.length === 0
                    ? "Create your first blog generation project"
                    : "View and manage all your Blu Blog Gen projects"}
                </p>
              </div>
              {permissions.canCreateProjects && (
                <Button
                  onClick={openNewProjectModal}
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
                  onClick={openNewProjectModal}
                  className="bg-accent hover:bg-accent/90 text-accent-foreground"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Project
                </Button>
              </div>
            ) : (
              <>
                {/* Project Statistics Overview */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Total Projects</p>
                        <p className="text-2xl font-bold text-foreground">{userData.projects.length}</p>
                      </div>
                      <div className="h-8 w-8 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 dark:text-blue-400 text-sm font-medium">📊</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Active Projects</p>
                        <p className="text-2xl font-bold text-foreground">{activeProjects.length}</p>
                      </div>
                      <div className="h-8 w-8 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center">
                        <span className="text-green-600 dark:text-green-400 text-sm font-medium">🔄</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Completed Projects</p>
                        <p className="text-2xl font-bold text-foreground">{completedProjects.length}</p>
                      </div>
                      <div className="h-8 w-8 bg-emerald-100 dark:bg-emerald-900/20 rounded-full flex items-center justify-center">
                        <span className="text-emerald-600 dark:text-emerald-400 text-sm font-medium">✅</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Failed Projects</p>
                        <p className="text-2xl font-bold text-foreground">{failedProjects.length}</p>
                      </div>
                      <div className="h-8 w-8 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
                        <span className="text-red-600 dark:text-red-400 text-sm font-medium">❌</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Projects Tabs */}
                <div className="mb-6">
                  <div className="border-b border-gray-200">
                    <nav className="-mb-px flex space-x-8">
                      <button
                        onClick={() => setActiveProjectsTab("active")}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                          activeProjectsTab === "active"
                            ? "border-blue-500 text-blue-600"
                            : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                        }`}
                      >
                        Active Projects ({activeProjects.length})
                      </button>
                      <button
                        onClick={() => setActiveProjectsTab("completed")}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                          activeProjectsTab === "completed"
                            ? "border-blue-500 text-blue-600"
                            : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                        }`}
                      >
                        Completed Projects ({completedProjects.length})
                      </button>
                      <button
                        onClick={() => setActiveProjectsTab("failed")}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                          activeProjectsTab === "failed"
                            ? "border-blue-500 text-blue-600"
                            : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                        }`}
                      >
                        Failed Projects ({failedProjects.length})
                      </button>
                    </nav>
                  </div>
                </div>

                {/* Tab Content */}
                <div className="space-y-8">
                  {activeProjectsTab === "active" && activeProjects.length > 0 && (
                   <div>
                     <p className="text-sm text-muted-foreground mb-4">
                       Projects that are in progress, partially generated, or ready to start
                     </p>
                     <ProjectList projects={activeProjects} loading={false} onProjectSelect={handleProjectSelect} onResume={handleResume} />
                   </div>
                 )}

                                   {activeProjectsTab === "completed" && completedProjects.length > 0 && (
                   <div>
                     <p className="text-sm text-muted-foreground mb-4">
                       Projects where all blogs have been generated and published to WordPress
                     </p>
                     <ProjectList projects={completedProjects} loading={false} onProjectSelect={handleProjectSelect} onResume={handleResume} />
                   </div>
                 )}

                                   {activeProjectsTab === "failed" && failedProjects.length > 0 && (
                   <div>
                     <p className="text-sm text-muted-foreground mb-4">
                       Projects that encountered errors during blog generation
                     </p>
                     <ProjectList projects={failedProjects} loading={false} onProjectSelect={handleProjectSelect} onResume={handleResume} />
                   </div>
                 )}

                 {/* Show message when no projects in selected tab */}
                 {((activeProjectsTab === "active" && activeProjects.length === 0) ||
                   (activeProjectsTab === "completed" && completedProjects.length === 0) ||
                   (activeProjectsTab === "failed" && failedProjects.length === 0)) && (
                   <div className="text-center py-16">
                     <div className="bg-muted/50 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                       <FileText className="h-8 w-8 text-muted-foreground" />
                     </div>
                     <h3 className="text-xl font-semibold text-foreground mb-2">
                       No {activeProjectsTab} projects
                     </h3>
                     <p className="text-muted-foreground mb-6">
                       {activeProjectsTab === "active" && "All your projects are either completed or failed."}
                       {activeProjectsTab === "completed" && "No projects have been completed yet."}
                       {activeProjectsTab === "failed" && "Great! No projects have failed."}
                     </p>
                   </div>
                 )}


                </div>
              </>
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

      {/* New Project Modal */}
      {showNewProject && userData && (
        <NewProjectModal
          key={`new-project-modal-${modalKey}`}
          onClose={() => setShowNewProject(false)}
          onSuccess={async (newProject) => {
            setShowNewProject(false)
            // Immediately add the new project to local state
            setUserData(prev => prev ? ({
              ...prev,
              projects: [newProject, ...prev.projects]
            }) : null)
            // Also refresh from database to ensure consistency
            setTimeout(async () => {
              await handleDataUpdate()
            }, 100)
          }}
          userId={user.id}
          userData={userData}
        />
      )}

      {/* Content Generation Modal */}
      {showContentGenerationModal && selectedProject && (
        <ContentGenerationModal
          isOpen={showContentGenerationModal}
          projectId={selectedProject.id}
          projectName={selectedProject.name}
          onClose={() => setShowContentGenerationModal(false)}
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
