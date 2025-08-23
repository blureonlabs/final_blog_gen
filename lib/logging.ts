import { storage } from "./storage"

export interface LogEntry {
  id: string
  timestamp: string
  level: "info" | "warning" | "error" | "success"
  category: "generation" | "publishing" | "api" | "system" | "user"
  message: string
  project_name?: string
  blog_title?: string
  details?: string
  user_id?: string
}

export interface AnalyticsData {
  totalUsers: number
  activeUsers: number
  totalProjects: number
  activeProjects: number
  totalBlogs: number
  publishedBlogs: number
  apiCalls: number
  revenue: number
  systemHealth: number
  serverUptime: number
  recentActivity: ActivityEntry[]
  topProjects: TopProject[]
  apiUsage: ApiUsageEntry[]
}

export interface ActivityEntry {
  id: string
  user: string
  action: string
  project: string
  time: string
  timestamp: string
}

export interface TopProject {
  name: string
  user: string
  blogs: number
  completion: number
}

export interface ApiUsageEntry {
  service: string
  calls: number
  cost: number
  status: "healthy" | "warning" | "error"
}

const LOGS_KEY = "bulk_blog_generator_logs"
const ANALYTICS_KEY = "bulk_blog_generator_analytics"

class Logger {
  private logs: LogEntry[] = []
  private maxLogs = 1000 // Keep only last 1000 logs

  constructor() {
    this.loadLogs()
  }

  private loadLogs() {
    if (typeof window === "undefined") return

    try {
      const savedLogs = localStorage.getItem(LOGS_KEY)
      if (savedLogs) {
        this.logs = JSON.parse(savedLogs)
      }
    } catch (error) {
      console.error("Error loading logs:", error)
    }
  }

  private saveLogs() {
    if (typeof window === "undefined") return

    try {
      // Keep only the most recent logs
      if (this.logs.length > this.maxLogs) {
        this.logs = this.logs.slice(-this.maxLogs)
      }
      localStorage.setItem(LOGS_KEY, JSON.stringify(this.logs))
    } catch (error) {
      console.error("Error saving logs:", error)
    }
  }

  log(
    level: LogEntry["level"],
    category: LogEntry["category"],
    message: string,
    options?: {
      project_name?: string
      blog_title?: string
      details?: string
      user_id?: string
    },
  ) {
    const logEntry: LogEntry = {
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date().toISOString(),
      level,
      category,
      message,
      ...options,
    }

    this.logs.unshift(logEntry) // Add to beginning for chronological order
    this.saveLogs()

    // Also log to console for development
    const consoleMethod = level === "error" ? "error" : level === "warning" ? "warn" : "log"
    console[consoleMethod](`[${category.toUpperCase()}] ${message}`, options?.details || "")
  }

  info(category: LogEntry["category"], message: string, options?: Parameters<typeof this.log>[3]) {
    this.log("info", category, message, options)
  }

  success(category: LogEntry["category"], message: string, options?: Parameters<typeof this.log>[3]) {
    this.log("success", category, message, options)
  }

  warning(category: LogEntry["category"], message: string, options?: Parameters<typeof this.log>[3]) {
    this.log("warning", category, message, options)
  }

  error(category: LogEntry["category"], message: string, options?: Parameters<typeof this.log>[3]) {
    this.log("error", category, message, options)
  }

  getLogs(filters?: {
    level?: LogEntry["level"]
    category?: LogEntry["category"]
    search?: string
    limit?: number
  }): LogEntry[] {
    let filteredLogs = [...this.logs]

    if (filters?.level) {
      filteredLogs = filteredLogs.filter((log) => log.level === filters.level)
    }

    if (filters?.category) {
      filteredLogs = filteredLogs.filter((log) => log.category === filters.category)
    }

    if (filters?.search) {
      const searchTerm = filters.search.toLowerCase()
      filteredLogs = filteredLogs.filter(
        (log) =>
          log.message.toLowerCase().includes(searchTerm) ||
          log.project_name?.toLowerCase().includes(searchTerm) ||
          log.blog_title?.toLowerCase().includes(searchTerm) ||
          log.details?.toLowerCase().includes(searchTerm),
      )
    }

    if (filters?.limit) {
      filteredLogs = filteredLogs.slice(0, filters.limit)
    }

    return filteredLogs
  }

  clearLogs() {
    this.logs = []
    this.saveLogs()
  }

  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2)
  }
}

class Analytics {
  generateAnalytics(): AnalyticsData {
    const userData = storage.getData()
    const logger = new Logger()
    const logs = logger.getLogs({ limit: 100 })

    // Calculate metrics from real data
    const totalProjects = userData.projects.length
    const activeProjects = userData.projects.filter((p) => p.status === "in_progress").length
    const completedProjects = userData.projects.filter((p) => p.status === "completed").length

    const totalBlogs = userData.projects.reduce((sum, project) => sum + project.total_blogs, 0)
    const publishedBlogs = userData.projects.reduce((sum, project) => sum + project.completed_blogs, 0)

    // Generate recent activity from logs and user data
    const recentActivity: ActivityEntry[] = []

    // Add project creation activities
    userData.projects.slice(-5).forEach((project, index) => {
      recentActivity.push({
        id: `activity-${index}`,
        user: "user@example.com",
        action: "Created new project",
        project: project.name,
        time: this.getRelativeTime(project.created_at),
        timestamp: project.created_at,
      })
    })

    // Add log-based activities
    logs.slice(0, 10).forEach((log, index) => {
      if (log.project_name) {
        recentActivity.push({
          id: `log-activity-${index}`,
          user: "user@example.com",
          action: log.message,
          project: log.project_name,
          time: this.getRelativeTime(log.timestamp),
          timestamp: log.timestamp,
        })
      }
    })

    // Sort by timestamp and take most recent
    recentActivity.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

    // Generate top projects
    const topProjects: TopProject[] = userData.projects
      .map((project) => ({
        name: project.name,
        user: "user@example.com",
        blogs: project.completed_blogs,
        completion: project.total_blogs > 0 ? Math.round((project.completed_blogs / project.total_blogs) * 100) : 0,
      }))
      .sort((a, b) => b.blogs - a.blogs)
      .slice(0, 5)

    // Generate API usage data
    const apiUsage: ApiUsageEntry[] = [
      {
        service: "OpenAI GPT-4",
        calls: publishedBlogs * 2, // Estimate 2 calls per blog
        cost: publishedBlogs * 0.03, // Estimate $0.03 per blog
        status: "healthy",
      },
      {
        service: "Google Gemini",
        calls: publishedBlogs * 1,
        cost: publishedBlogs * 0.02,
        status: "healthy",
      },
      {
        service: "SERP API",
        calls: publishedBlogs * 3, // Research calls
        cost: publishedBlogs * 0.01,
        status: userData.apiKeys.filter((k) => k.service === "serp").length > 0 ? "healthy" : "warning",
      },
      {
        service: "WordPress API",
        calls: publishedBlogs,
        cost: 0,
        status: userData.wordpressAccounts.length > 0 ? "healthy" : "warning",
      },
    ]

    return {
      totalUsers: 1, // Single user for now
      activeUsers: 1,
      totalProjects,
      activeProjects,
      totalBlogs,
      publishedBlogs,
      apiCalls: apiUsage.reduce((sum, api) => sum + api.calls, 0),
      revenue: this.calculateRevenue(userData.subscription.plan),
      systemHealth: this.calculateSystemHealth(userData, logs),
      serverUptime: 99.9, // Mock uptime
      recentActivity: recentActivity.slice(0, 5),
      topProjects,
      apiUsage,
    }
  }

  private getRelativeTime(timestamp: string): string {
    const now = new Date()
    const time = new Date(timestamp)
    const diffMs = now.getTime() - time.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffMins < 1) return "Just now"
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`
    return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`
  }

  private calculateRevenue(plan: string): number {
    const planPricing = {
      free: 0,
      starter: 499,
      professional: 1499,
      enterprise: 4999,
    }
    return planPricing[plan as keyof typeof planPricing] || 0
  }

  private calculateSystemHealth(userData: any, logs: LogEntry[]): number {
    let health = 100

    // Reduce health based on errors in logs
    const errorLogs = logs.filter((log) => log.level === "error")
    health -= errorLogs.length * 2

    // Reduce health if no API keys configured
    if (userData.apiKeys.length === 0) health -= 20

    // Reduce health if no WordPress accounts
    if (userData.wordpressAccounts.length === 0) health -= 10

    return Math.max(health, 0)
  }
}

// Export singleton instances
export const logger = new Logger()
export const analytics = new Analytics()
