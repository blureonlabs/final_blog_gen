import { supabase } from "./supabase"
import { authManager } from "./auth"

export interface ActivityLog {
  id?: string
  user_id?: string
  action: string
  level: "info" | "warning" | "error" | "success"
  category: "user" | "project" | "blog" | "api" | "system" | "auth"
  timestamp?: string
  metadata?: any
}

export interface LogFilters {
  level?: ActivityLog["level"]
  category?: ActivityLog["category"]
  project_id?: string
  start_date?: string
  end_date?: string
  limit?: number
}

class ActivityLogger {
  private maxLogs = 1000 // Keep only last 1000 logs per user

  /**
   * Log an activity event to the database
   */
  async log(
    action: string,
    category: ActivityLog["category"] = "user",
    level: ActivityLog["level"] = "info",
    metadata?: any
  ): Promise<string | null> {
    try {
      console.log("🔍 Activity Logger: Starting log entry...")
      
      const currentUser = authManager.getAuthState().user
      if (!currentUser) {
        console.warn("❌ Cannot log: User not authenticated")
        return null
      }

      console.log("✅ User authenticated:", currentUser.id)

      const logEntry: ActivityLog = {
        user_id: currentUser.id,
        action,
        level,
        category,
        timestamp: new Date().toISOString(),
        metadata: metadata || null
      }

      console.log("📝 Log entry prepared:", logEntry)

      // Insert log into Supabase
      console.log("🚀 Attempting to insert into activity_logs table...")
      const { data, error } = await supabase
        .from('activity_logs')
        .insert(logEntry)
        .select('id')
        .single()

      if (error) {
        console.error("❌ Failed to save log to Supabase:", error)
        console.error("🔍 Error details:", {
          code: error.code,
          message: error.message,
          details: error.details,
          hint: error.hint
        })
        return null
      }

      console.log("✅ Log saved successfully! ID:", data?.id)

      // Clean up old logs to maintain performance
      await this.cleanupOldLogs(currentUser.id)

      return data?.id || null

    } catch (error) {
      console.error("💥 Error in activity logging:", error)
      return null
    }
  }

  /**
   * Log user login
   */
  async logLogin(email: string): Promise<string | null> {
    console.log("🔐 Logging login for user:", email)
    const result = await this.log(
      "User logged in",
      "auth",
      "info",
      { email, timestamp: new Date().toISOString() }
    )
    console.log("🔐 Login log result:", result)
    return result
  }

  /**
   * Log user logout
   */
  async logLogout(email: string): Promise<string | null> {
    return this.log(
      "User logged out",
      "auth",
      "info",
      { email, timestamp: new Date().toISOString() }
    )
  }

  /**
   * Log project creation
   */
  async logProjectCreated(projectName: string, projectId: string, numBlogs: number): Promise<string | null> {
    return this.log(
      "Project created",
      "project",
      "info",
      { project_name: projectName, project_id: projectId, num_blogs: numBlogs }
    )
  }

  /**
   * Log project status change
   */
  async logProjectStatusChange(projectName: string, projectId: string, oldStatus: string, newStatus: string): Promise<string | null> {
    return this.log(
      "Project status changed",
      "project",
      "info",
      { project_name: projectName, project_id: projectId, old_status: oldStatus, new_status: newStatus }
    )
  }

  /**
   * Log blog creation
   */
  async logBlogCreated(blogTitle: string, blogId: string, projectId: string): Promise<string | null> {
    return this.log(
      "Blog created",
      "blog",
      "info",
      { blog_title: blogTitle, blog_id: blogId, project_id: projectId }
    )
  }

  /**
   * Log blog status change
   */
  async logBlogStatusChange(blogTitle: string, blogId: string, oldStatus: string, newStatus: string): Promise<string | null> {
    return this.log(
      "Blog status changed",
      "blog",
      "info",
      { blog_title: blogTitle, blog_id: blogId, old_status: oldStatus, new_status: newStatus }
    )
  }

  /**
   * Log API key addition
   */
  async logApiKeyAdded(service: string, name: string, isDefault: boolean): Promise<string | null> {
    return this.log(
      "API key added",
      "api",
      "info",
      { service, name, is_default: isDefault }
    )
  }

  /**
   * Log API key removal
   */
  async logApiKeyRemoved(service: string, name: string): Promise<string | null> {
    return this.log(
      "API key removed",
      "api",
      "warning",
      { service, name }
    )
  }

  /**
   * Log API key activation change
   */
  async logApiKeyActivationChange(service: string, name: string, oldActive: boolean, newActive: boolean): Promise<string | null> {
    return this.log(
      "API key activation changed",
      "api",
      "info",
      { service, name, old_active: oldActive, new_active: newActive }
    )
  }

  /**
   * Log WordPress account addition
   */
  async logWordPressAccountAdded(name: string, siteUrl: string): Promise<string | null> {
    return this.log(
      "WordPress account added",
      "api",
      "info",
      { name, site_url: siteUrl }
    )
  }

  /**
   * Log WordPress account removal
   */
  async logWordPressAccountRemoved(name: string, siteUrl: string): Promise<string | null> {
    return this.log(
      "WordPress account removed",
      "api",
      "warning",
      { name, site_url: siteUrl }
    )
  }

  /**
   * Log content generation start
   */
  async logContentGenerationStart(projectName: string, projectId: string, blogTitle?: string): Promise<string | null> {
    return this.log(
      "Content generation started",
      "blog",
      "info",
      { project_name: projectName, project_id: projectId, blog_title: blogTitle }
    )
  }

  /**
   * Log content generation completion
   */
  async logContentGenerationComplete(projectName: string, projectId: string, blogTitle?: string, duration?: number): Promise<string | null> {
    return this.log(
      "Content generation completed",
      "blog",
      "success",
      { project_name: projectName, project_id: projectId, blog_title: blogTitle, duration_seconds: duration }
    )
  }

  /**
   * Log content generation error
   */
  async logContentGenerationError(projectName: string, projectId: string, error: string, blogTitle?: string): Promise<string | null> {
    return this.log(
      "Content generation failed",
      "blog",
      "error",
      { project_name: projectName, project_id: projectId, blog_title: blogTitle, error_message: error }
    )
  }

  /**
   * Log user settings change
   */
  async logSettingsChange(setting: string, oldValue: any, newValue: any): Promise<string | null> {
    return this.log(
      "User settings changed",
      "user",
      "info",
      { setting, old_value: oldValue, new_value: newValue }
    )
  }

  /**
   * Log admin action
   */
  async logAdminAction(action: string, targetUser?: string, details?: any): Promise<string | null> {
    const currentUser = authManager.getAuthState().user
    if (currentUser?.role !== 'admin') {
      console.warn("Only admins can log admin actions")
      return null
    }

    return this.log(
      `Admin: ${action}`,
      "system",
      "info",
      { target_user: targetUser, ...details }
    )
  }

  /**
   * Get logs for the current user or all logs for admins
   */
  async getLogs(filters: LogFilters = {}): Promise<ActivityLog[]> {
    try {
      const currentUser = authManager.getAuthState().user
      if (!currentUser) {
        console.warn("Cannot get logs: User not authenticated")
        return []
      }

      let query = supabase
        .from('activity_logs')
        .select('*')
        .order('timestamp', { ascending: false })

      // Apply filters
      if (filters.level) {
        query = query.eq('level', filters.level)
      }
      if (filters.category) {
        query = query.eq('category', filters.category)
      }
      if (filters.project_id) {
        query = query.contains('metadata', { project_id: filters.project_id })
      }
      if (filters.start_date) {
        query = query.gte('timestamp', filters.start_date)
      }
      if (filters.end_date) {
        query = query.lte('timestamp', filters.end_date)
      }

      // Regular users only see their own logs, admins see all
      if (currentUser.role !== 'admin') {
        query = query.eq('user_id', currentUser.id)
      }

      // Apply limit
      if (filters.limit) {
        query = query.limit(filters.limit)
      } else {
        query = query.limit(100) // Default limit
      }

      const { data, error } = await query

      if (error) {
        console.error("Failed to fetch logs:", error)
        return []
      }

      return data || []

    } catch (error) {
      console.error("Error fetching logs:", error)
      return []
    }
  }

  /**
   * Export logs as JSON
   */
  async exportLogs(filters: LogFilters = {}): Promise<string> {
    const logs = await this.getLogs({ ...filters, limit: 1000 })
    return JSON.stringify(logs, null, 2)
  }

  /**
   * Clean up old logs to maintain performance
   */
  private async cleanupOldLogs(userId: string): Promise<void> {
    try {
      // Get count of user's logs
      const { count } = await supabase
        .from('activity_logs')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', userId)

      if (count && count > this.maxLogs) {
        // Delete old logs beyond the limit
        const { error } = await supabase
          .from('activity_logs')
          .delete()
          .eq('user_id', userId)
          .lt('timestamp', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString()) // Delete logs older than 30 days

        if (error) {
          console.warn("Failed to cleanup old logs:", error)
        }
      }
    } catch (error) {
      console.warn("Error during log cleanup:", error)
    }
  }
}

// Create singleton instance
export const activityLogger = new ActivityLogger()

// Export individual logging functions for convenience
export const {
  logLogin,
  logLogout,
  logProjectCreated,
  logProjectStatusChange,
  logBlogCreated,
  logBlogStatusChange,
  logApiKeyAdded,
  logApiKeyRemoved,
  logApiKeyActivationChange,
  logWordPressAccountAdded,
  logWordPressAccountRemoved,
  logContentGenerationStart,
  logContentGenerationComplete,
  logContentGenerationError,
  logSettingsChange,
  logAdminAction,
  getLogs,
  exportLogs
} = activityLogger
