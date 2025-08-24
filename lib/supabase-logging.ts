import { supabase } from "./supabase"
import { authManager } from "./auth"

export interface LogEntry {
  id: string
  user_id?: string
  action: string // Changed from 'message' to 'action' to match DB schema
  level: "info" | "warning" | "error" | "success"
  category: "generation" | "publishing" | "api" | "system" | "user"
  timestamp: string
  details?: any
}

export interface LogFilters {
  level?: LogEntry["level"]
  category?: LogEntry["category"]
  search?: string
  limit?: number
  project_id?: string
  start_date?: string
  end_date?: string
}

class SupabaseLogger {
  private maxLogs = 1000 // Keep only last 1000 logs per user

  async log(
    level: LogEntry["level"],
    category: LogEntry["category"],
    message: string,
    options?: {
      project_name?: string
      blog_title?: string
      details?: any
      metadata?: any
    },
  ): Promise<void> {
    try {
      // Check if Supabase is configured
      if (!supabase || !process.env.NEXT_PUBLIC_SUPABASE_URL) {
        console.warn('Supabase not configured, using console logging only')
        this.logToConsole(level, category, message, options)
        return
      }

      const currentUser = authManager.getAuthState().user
      if (!currentUser) {
        console.warn("Cannot log: User not authenticated")
        this.logToConsole(level, category, message, options)
        return
      }

      const logEntry = {
        user_id: currentUser.id,
        action: message, // Use 'action' instead of 'message' to match DB schema
        level,
        category,
        timestamp: new Date().toISOString(),
        details: options?.details || null, // Only include details if they exist
      }

      // Insert log into Supabase
      console.log("Attempting to insert log:", logEntry) // Debug log
      const { error } = await supabase
        .from('activity_logs')
        .insert(logEntry)

      if (error) {
        console.error("Failed to save log to Supabase:", error)
        // Fallback to console logging
        this.logToConsole(level, category, message, options)
        return
      }

      console.log("Log successfully saved to Supabase") // Debug log

      // Clean up old logs to maintain performance
      await this.cleanupOldLogs(currentUser.id)

      // Also log to console for development
      this.logToConsole(level, category, message, options)

    } catch (error) {
      console.error("Error in Supabase logging:", error)
      // Fallback to console logging
      this.logToConsole(level, category, message, options)
    }
  }

  private logToConsole(
    level: LogEntry["level"],
    category: LogEntry["category"],
    message: string,
    options?: any,
  ) {
    const consoleMethod = level === "error" ? "error" : level === "warning" ? "warn" : "log"
    console[consoleMethod](`[${category.toUpperCase()}] ${message}`, options?.details || "")
  }

  async getLogs(filters: LogFilters = {}): Promise<LogEntry[]> {
    try {
      // Check if Supabase is configured
      if (!supabase || !process.env.NEXT_PUBLIC_SUPABASE_URL) {
        console.warn('Supabase not configured, returning empty logs')
        return []
      }

      const currentUser = authManager.getAuthState().user
      if (!currentUser) {
        console.warn("Cannot fetch logs: User not authenticated")
        return []
      }

      let query = supabase
        .from('activity_logs')
        .select('*')
        .eq('user_id', currentUser.id)
        .order('timestamp', { ascending: false })

      // Apply filters
      if (filters.level) {
        query = query.eq('level', filters.level)
      }

      if (filters.category) {
        query = query.eq('category', filters.category)
      }

      if (filters.project_id) {
        query = query.eq('project_name', filters.project_id)
      }

      if (filters.start_date) {
        query = query.gte('timestamp', filters.start_date)
      }

      if (filters.end_date) {
        query = query.lte('timestamp', filters.end_date)
      }

      if (filters.limit) {
        query = query.limit(filters.limit)
      }

      const { data, error } = await query

      if (error) {
        console.error("Failed to fetch logs from Supabase:", error)
        return []
      }

      // Apply search filter if provided
      let filteredLogs = data || []
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase()
        filteredLogs = filteredLogs.filter(
          (log) =>
            log.action.toLowerCase().includes(searchTerm) || // Use 'action' instead of 'message'
            (log.details && JSON.stringify(log.details).toLowerCase().includes(searchTerm)),
        )
      }

      return filteredLogs

    } catch (error) {
      console.error("Error fetching logs:", error)
      return []
    }
  }

  async getLogsByProject(projectId: string, limit: number = 50): Promise<LogEntry[]> {
    return this.getLogs({ project_id: projectId, limit })
  }

  async getRecentLogs(limit: number = 100): Promise<LogEntry[]> {
    return this.getLogs({ limit })
  }

  async getLogsByLevel(level: LogEntry["level"], limit: number = 100): Promise<LogEntry[]> {
    return this.getLogs({ level, limit })
  }

  async getLogsByCategory(category: LogEntry["category"], limit: number = 100): Promise<LogEntry[]> {
    return this.getLogs({ category, limit })
  }

  async searchLogs(searchTerm: string, limit: number = 100): Promise<LogEntry[]> {
    return this.getLogs({ search: searchTerm, limit })
  }

  async clearLogs(): Promise<boolean> {
    try {
      const currentUser = authManager.getAuthState().user
      if (!currentUser) {
        console.warn("Cannot clear logs: User not authenticated")
        return false
      }

      const { error } = await supabase
        .from('activity_logs')
        .delete()
        .eq('user_id', currentUser.id)

      if (error) {
        console.error("Failed to clear logs from Supabase:", error)
        return false
      }

      return true

    } catch (error) {
      console.error("Error clearing logs:", error)
      return false
    }
  }

  async exportLogs(): Promise<string> {
    try {
      const logs = await this.getLogs({ limit: 10000 }) // Get all logs
      return JSON.stringify(logs, null, 2)
    } catch (error) {
      console.error("Error exporting logs:", error)
      return "[]"
    }
  }

  private async cleanupOldLogs(userId: string): Promise<void> {
    try {
      // Get total count of logs for this user
      const { count, error } = await supabase
        .from('activity_logs')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', userId)

      if (error || !count || count <= this.maxLogs) {
        return
      }

      // Delete old logs beyond the limit
      const logsToDelete = count - this.maxLogs

      const { error: deleteError } = await supabase
        .from('activity_logs')
        .delete()
        .eq('user_id', userId)
        .lt('timestamp', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()) // Delete logs older than 24 hours
        .limit(logsToDelete)

      if (deleteError) {
        console.warn("Failed to cleanup old logs:", deleteError)
      }

    } catch (error) {
      console.warn("Error during log cleanup:", error)
    }
  }

  // Convenience methods
  async info(category: LogEntry["category"], message: string, options?: any): Promise<void> {
    await this.log("info", category, message, options)
  }

  async success(category: LogEntry["category"], message: string, options?: any): Promise<void> {
    await this.log("success", category, message, options)
  }

  async warning(category: LogEntry["category"], message: string, options?: any): Promise<void> {
    await this.log("warning", category, message, options)
  }

  async error(category: LogEntry["category"], message: string, options?: any): Promise<void> {
    await this.log("error", category, message, options)
  }
}

// Export singleton instance
export const supabaseLogger = new SupabaseLogger()
