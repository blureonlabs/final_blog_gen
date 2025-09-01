"use client"

import { useState, useEffect } from "react"
import { supabaseLogger, type LogEntry } from "@/lib/supabase-logging"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Download, Trash2, RefreshCw, Hash, Calendar, User, Settings, AlertCircle, CheckCircle, Clock } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { memo } from "react"

// Memoized LogCard component for better performance
const LogCard = memo(({ log }: { log: LogEntry }) => {
  const getLevelColor = (level: string) => {
    switch (level) {
      case "error":
        return "destructive"
      case "warning":
        return "secondary"
      case "info":
        return "default"
      default:
        return "outline"
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "generation":
        return "bg-blue-100 text-blue-800"
      case "user":
        return "bg-green-100 text-green-800"
      case "system":
        return "bg-gray-100 text-gray-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const getMetadataIcon = (key: string) => {
    const keyLower = key.toLowerCase()
    if (keyLower.includes('id') || keyLower.includes('hash')) return <Hash className="h-3 w-3" />
    if (keyLower.includes('date') || keyLower.includes('time') || keyLower.includes('created') || keyLower.includes('updated')) return <Calendar className="h-3 w-3" />
    if (keyLower.includes('user') || keyLower.includes('name') || keyLower.includes('email')) return <User className="h-3 w-3" />
    if (keyLower.includes('model') || keyLower.includes('ai') || keyLower.includes('provider')) return <Settings className="h-3 w-3" />
    if (keyLower.includes('error') || keyLower.includes('failed') || keyLower.includes('warning')) return <AlertCircle className="h-3 w-3" />
    if (keyLower.includes('success') || keyLower.includes('completed') || keyLower.includes('generated')) return <CheckCircle className="h-3 w-3" />
    if (keyLower.includes('progress') || keyLower.includes('count') || keyLower.includes('number')) return <Clock className="h-3 w-3" />
    return <Hash className="h-3 w-3" />
  }

  const getValueColor = (key: string, value: any) => {
    const keyLower = key.toLowerCase()
    if (keyLower.includes('error') || keyLower.includes('failed')) return 'text-red-600'
    if (keyLower.includes('success') || keyLower.includes('completed')) return 'text-green-600'
    if (keyLower.includes('warning')) return 'text-yellow-600'
    if (keyLower.includes('progress') || keyLower.includes('count') || keyLower.includes('number')) return 'text-blue-600'
    if (typeof value === 'boolean') return value ? 'text-green-600' : 'text-red-600'
    return 'text-muted-foreground'
  }

  const formatValue = (key: string, value: any) => {
    if (typeof value === "boolean") {
      return value ? "Yes" : "No"
    }
    if (typeof value === "number") {
      return value.toLocaleString()
    }
    if (typeof value === "string") {
      const keyLower = key.toLowerCase()
      if (keyLower.includes('url') || keyLower.includes('link')) {
        return (
          <a 
            href={value} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 underline break-all"
          >
            {value}
          </a>
        )
      }
      if (value.length > 100) {
        return (
          <span className="break-all">
            {value.substring(0, 100)}...
            <span className="text-xs text-muted-foreground ml-1">(truncated)</span>
          </span>
        )
      }
    }
    return String(value)
  }

  return (
    <Card className={`hover:shadow-md transition-shadow border-l-4 ${
      log.level === 'error' ? 'border-l-red-500 bg-red-50/30' :
      log.level === 'warning' ? 'border-l-yellow-500 bg-yellow-50/30' :
      log.level === 'info' ? 'border-l-blue-500 bg-blue-50/30' :
      'border-l-gray-500 bg-gray-50/30'
    }`}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant={getLevelColor(log.level)} className="text-xs">
                {log.level.toUpperCase()}
              </Badge>
              <Badge className={`text-xs ${getCategoryColor(log.category)}`}>
                {log.category}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {new Date(log.timestamp || "").toLocaleString()}
              </span>
            </div>
            <p className="text-sm font-medium text-foreground">{log.action}</p>
            {log.metadata && Object.keys(log.metadata).length > 0 && (
              <div className="text-xs text-muted-foreground bg-white/80 p-4 rounded-lg border shadow-sm">
                <div className="font-medium mb-3 text-foreground flex items-center gap-2">
                  <span className="text-blue-600">📋</span>
                  <span>Details</span>
                </div>
                <div className="space-y-3">
                  {Object.entries(log.metadata).map(([key, value]) => {
                    // Skip if value is null, undefined, or empty
                    if (value === null || value === undefined || value === "") return null;
                    
                    // Handle different value types
                    if (typeof value === "object" && value !== null) {
                      // If it's a details object, render its contents
                      if (key === "details") {
                        return (
                          <div key={key} className="space-y-1">
                            {Object.entries(value).map(([detailKey, detailValue]) => {
                              if (detailValue === null || detailValue === undefined || detailValue === "") return null;
                              return (
                                <div key={detailKey} className="flex items-start gap-2">
                                  <div className="flex items-center gap-2 min-w-[90px]">
                                    <span className="text-muted-foreground">
                                      {getMetadataIcon(detailKey)}
                                    </span>
                                    <span className="font-medium text-foreground capitalize">
                                      {detailKey.replace(/_/g, " ")}:
                                    </span>
                                  </div>
                                  <span className={`flex-1 ${getValueColor(detailKey, detailValue)}`}>
                                    {formatValue(detailKey, detailValue)}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        );
                      } else {
                        // For other objects, show as key-value pairs
                        return (
                          <div key={key} className="space-y-1">
                            <div className="font-medium text-foreground capitalize mb-1">
                              {key.replace(/_/g, " ")}:
                            </div>
                            {Object.entries(value).map(([objKey, objValue]) => {
                              if (objValue === null || objValue === undefined || objValue === "") return null;
                              return (
                                <div key={objKey} className="flex items-start gap-2 ml-4">
                                  <div className="flex items-center gap-2 min-w-[70px]">
                                    <span className="text-muted-foreground">
                                      {getMetadataIcon(objKey)}
                                    </span>
                                    <span className="font-medium text-muted-foreground capitalize">
                                      {objKey.replace(/_/g, " ")}:
                                    </span>
                                  </div>
                                  <span className={`flex-1 ${getValueColor(objKey, objValue)}`}>
                                    {formatValue(objKey, objValue)}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        );
                      }
                    } else {
                      // Simple key-value pairs
                      return (
                        <div key={key} className="flex items-start gap-2">
                          <div className="flex items-center gap-2 min-w-[90px]">
                            <span className="text-muted-foreground">
                              {getMetadataIcon(key)}
                            </span>
                            <span className="font-medium text-foreground capitalize">
                              {key.replace(/_/g, " ")}:
                            </span>
                          </div>
                          <span className={`flex-1 ${getValueColor(key, value)}`}>
                            {formatValue(key, value)}
                          </span>
                        </div>
                      );
                    }
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
})

LogCard.displayName = 'LogCard'

export function Logs() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [totalCount, setTotalCount] = useState(0)
  const [currentPage, setCurrentPage] = useState(0)
  const { toast } = useToast()

  const LOGS_PER_PAGE = 20

  useEffect(() => {
    loadLogs(true)
  }, [])

  const loadLogs = async (reset = false) => {
    try {
      if (reset) {
        setLoading(true)
        setCurrentPage(0)
        setLogs([])
      } else {
        setLoadingMore(true)
      }

      const offset = reset ? 0 : currentPage * LOGS_PER_PAGE
      const [newLogs, count] = await Promise.all([
        supabaseLogger.getLogs(LOGS_PER_PAGE, offset),
        reset ? supabaseLogger.getLogsCount() : Promise.resolve(totalCount)
      ])

      if (reset) {
        setLogs(newLogs || [])
        setTotalCount(count)
      } else {
        setLogs(prev => [...prev, ...(newLogs || [])])
      }

      setHasMore((newLogs?.length || 0) === LOGS_PER_PAGE)
      setCurrentPage(prev => prev + 1)
    } catch (error) {
      console.error("Error loading logs:", error)
      toast({
        title: "Error",
        description: "Failed to load logs",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await loadLogs(true)
    setRefreshing(false)
    toast({
      title: "Success",
      description: "Logs refreshed",
    })
  }

  const handleLoadMore = () => {
    if (!loadingMore && hasMore) {
      loadLogs(false)
    }
  }

  const handleExport = async () => {
    try {
      const csvContent = await supabaseLogger.exportLogs()
      if (csvContent) {
        const blob = new Blob([csvContent], { type: "text/csv" })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = `activity-logs-${new Date().toISOString().split("T")[0]}.csv`
        a.click()
        window.URL.revokeObjectURL(url)
        toast({
          title: "Success",
          description: "Logs exported successfully",
        })
      }
    } catch (error) {
      console.error("Error exporting logs:", error)
      toast({
        title: "Error",
        description: "Failed to export logs",
        variant: "destructive",
      })
    }
  }

  const handleClear = async () => {
    if (confirm("Are you sure you want to clear all logs? This action cannot be undone.")) {
      try {
        const success = await supabaseLogger.clearLogs()
        if (success) {
          setLogs([])
          toast({
            title: "Success",
            description: "All logs cleared",
          })
        }
      } catch (error) {
        console.error("Error clearing logs:", error)
        toast({
          title: "Error",
          description: "Failed to clear logs",
          variant: "destructive",
        })
      }
    }
  }



  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-foreground">Activity Logs</h2>
          <p className="text-lg text-muted-foreground">
            View and manage your application activity logs
            {totalCount > 0 && (
              <span className="ml-2 text-sm bg-muted px-2 py-1 rounded">
                {totalCount} total logs
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button onClick={handleExport} variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button onClick={handleClear} variant="destructive" size="sm">
            <Trash2 className="h-4 w-4 mr-2" />
            Clear All
          </Button>
        </div>
      </div>

      {logs.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="bg-muted/50 rounded-full w-16 h-16 flex items-center justify-center mb-4">
              <RefreshCw className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-2">No logs yet</h3>
            <p className="text-muted-foreground text-center">
              Activity logs will appear here as you use the application
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {logs.map((log, index) => (
            <LogCard key={log.id || index} log={log} />
          ))}
          
          {hasMore && (
            <div className="flex justify-center py-4">
              <Button
                onClick={handleLoadMore}
                disabled={loadingMore}
                variant="outline"
                size="sm"
              >
                {loadingMore ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Loading...
                  </>
                ) : (
                  <>
                    Load More ({totalCount - logs.length} remaining)
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
