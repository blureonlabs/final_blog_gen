"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { databaseChecker, type DatabaseHealth, type TableStatus } from "@/lib/database-check"
import { checkEnvironment, getEnvironmentRecommendations } from "@/lib/environment-check"
import { usePermissions } from "@/lib/use-permissions"
import { RefreshCw, CheckCircle, AlertTriangle, XCircle, Database, User, Table, Activity, Settings } from "lucide-react"

export function DatabaseHealth() {
  const [health, setHealth] = useState<DatabaseHealth | null>(null)
  const [loading, setLoading] = useState(false)
  const [lastChecked, setLastChecked] = useState<Date | null>(null)
  const [envStatus, setEnvStatus] = useState(checkEnvironment())
  const permissions = usePermissions()

  useEffect(() => {
    runHealthCheck()
  }, [])

  const runHealthCheck = async () => {
    console.log('Starting health check...')
    setLoading(true)
    try {
      const result = await databaseChecker.checkDatabaseHealth()
      console.log('Health check result:', result)
      setHealth(result)
      setEnvStatus(checkEnvironment())
      setLastChecked(new Date())
    } catch (error) {
      console.error('Health check failed:', error)
    } finally {
      setLoading(false)
      console.log('Health check completed')
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case "warning":
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />
      case "error":
        return <XCircle className="w-5 h-5 text-red-600" />
      default:
        return <AlertTriangle className="w-5 h-5 text-gray-600" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "bg-green-100 text-green-800 border-green-200"
      case "warning":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "error":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getTableIcon = (tableName: string) => {
    switch (tableName) {
      case "users":
        return <User className="w-4 h-4" />
      case "activity_logs":
        return <Activity className="w-4 h-4" />
      case "projects":
        return <Table className="w-4 h-4" />
      case "blogs":
        return <Table className="w-4 h-4" />
      case "wordpress_accounts":
        return <Settings className="w-4 h-4" />
      case "api_keys":
        return <Settings className="w-4 h-4" />
      default:
        return <Table className="w-4 h-4" />
    }
  }

  if (!health) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            Database Health Check
          </CardTitle>
          <CardDescription>
            Checking database connectivity and table status...
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Overall Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Database className="w-5 h-5" />
                Database Health Status
              </CardTitle>
              <CardDescription>
                Overall database health and table status
                {lastChecked && (
                  <span className="ml-2 text-xs text-gray-500">
                    Last checked: {lastChecked.toLocaleTimeString()}
                  </span>
                )}
              </CardDescription>
            </div>
            <Button
              onClick={runHealthCheck}
              disabled={loading}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                if (permissions.isAdmin) {
                  const actualCounts = await databaseChecker.getActualTableCounts()
                  console.log('Actual table counts:', actualCounts)
                  alert(`Actual table counts:\n${Object.entries(actualCounts).map(([table, count]) => `${table}: ${count} rows`).join('\n')}`)
                }
              }}
              disabled={!permissions.isAdmin}
              className="flex items-center gap-2"
              title="Show actual table counts (Admin only)"
            >
              <Database className="w-4 h-4" />
              Show Actual Counts
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-6">
            {getStatusIcon(health.overall_status)}
            <div>
              <h3 className="text-lg font-semibold">Overall Status</h3>
              <Badge className={`${getStatusColor(health.overall_status)}`}>
                {health.overall_status.toUpperCase()}
              </Badge>
            </div>
          </div>

          {/* Connection Status */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Database className="w-4 h-4" />
                <span className="font-medium">Database Connection</span>
              </div>
              <Badge className={health.connection_working ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                {health.connection_working ? "Connected" : "Failed"}
              </Badge>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <User className="w-4 h-4" />
                <span className="font-medium">Authentication</span>
              </div>
              <Badge className={health.user_authenticated ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                {health.user_authenticated ? "Authenticated" : "Not Authenticated"}
              </Badge>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Settings className="w-4 h-4" />
                <span className="font-medium">Environment</span>
              </div>
              <Badge className={envStatus.all_configured ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                {envStatus.all_configured ? "Configured" : "Missing Vars"}
              </Badge>
            </div>
          </div>

          {/* Issues */}
          {health.issues.length > 0 && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <h4 className="font-medium text-red-800 mb-2">Issues Found:</h4>
              <ul className="text-sm text-red-700 space-y-1">
                {health.issues.map((issue, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-red-500">•</span>
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Table Status */}
      <Card>
        <CardHeader>
          <CardTitle>Table Status</CardTitle>
          <CardDescription>
            Status of all required database tables
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {health.tables.map((table) => (
              <div key={table.table_name} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  {getTableIcon(table.table_name)}
                  <div>
                    <h4 className="font-medium">{table.table_name}</h4>
                    <p className="text-sm text-gray-600">
                      {table.exists ? `${table.row_count} rows` : "Table missing"}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  {table.exists && table.accessible ? (
                    <Badge className="bg-green-100 text-green-800">✓ Healthy</Badge>
                  ) : table.exists && !table.accessible ? (
                    <Badge className="bg-yellow-100 text-yellow-800">⚠ Access Issue</Badge>
                  ) : (
                    <Badge className="bg-red-100 text-red-800">✗ Missing</Badge>
                  )}
                  
                  {table.error && (
                    <span className="text-xs text-red-600" title={table.error}>
                      Error
                    </span>
                  )}
                </div>
              </div>
            ))}
            

          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      {health.overall_status !== "healthy" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-yellow-800">Recommendations</CardTitle>
            <CardDescription>
              Steps to resolve database issues
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              {!health.connection_working && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="font-medium text-blue-800 mb-1">Database Connection Issue</p>
                  <p className="text-blue-700">Check your Supabase project URL and API keys in the environment variables.</p>
                </div>
              )}
              
              {!health.user_authenticated && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="font-medium text-blue-800 mb-1">Authentication Issue</p>
                  <p className="text-blue-700">Make sure you're logged in to the application.</p>
                </div>
              )}
              

              
              {health.tables.some(t => t.exists && !t.accessible) && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="font-medium text-blue-800 mb-1">Permission Issues</p>
                  <p className="text-blue-700">Check Row Level Security (RLS) policies in your Supabase dashboard.</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
