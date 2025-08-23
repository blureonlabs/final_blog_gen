import { supabase } from "./supabase"
import { authManager } from "./auth"

export interface TableStatus {
  table_name: string
  exists: boolean
  row_count: number
  accessible: boolean
  error?: string
}

export interface DatabaseHealth {
  overall_status: "healthy" | "warning" | "error"
  tables: TableStatus[]
  user_authenticated: boolean
  connection_working: boolean
  issues: string[]
}

class DatabaseChecker {
  private requiredTables = [
    'users',
    'activity_logs',
    'projects',
    'blogs',
    'wordpress_accounts',
    'api_keys'
  ]

  async checkDatabaseHealth(): Promise<DatabaseHealth> {
    console.log('DatabaseChecker: Starting health check...')
    const health: DatabaseHealth = {
      overall_status: "healthy",
      tables: [],
      user_authenticated: false,
      connection_working: false,
      issues: []
    }

    try {
      // Check if user is authenticated
      const authState = authManager.getAuthState()
      console.log('DatabaseChecker: Auth state:', authState)
      health.user_authenticated = authState.isAuthenticated

      if (!health.user_authenticated) {
        console.log('DatabaseChecker: User not authenticated')
        health.overall_status = "error"
        health.issues.push("User not authenticated")
        return health
      }

      // Check database connection
      console.log('DatabaseChecker: Testing database connection...')
      const { data: connectionTest, error: connectionError } = await supabase
        .from('users')
        .select('count')
        .limit(1)

      if (connectionError) {
        console.log('DatabaseChecker: Connection failed:', connectionError)
        health.connection_working = false
        health.overall_status = "error"
        health.issues.push(`Database connection failed: ${connectionError.message}`)
      } else {
        console.log('DatabaseChecker: Connection successful')
        health.connection_working = true
      }

      // Check each required table
      console.log('DatabaseChecker: Checking tables:', this.requiredTables)
      for (const tableName of this.requiredTables) {
        console.log(`DatabaseChecker: Checking table: ${tableName}`)
        const tableStatus = await this.checkTable(tableName)
        console.log(`DatabaseChecker: Table ${tableName} status:`, tableStatus)
        health.tables.push(tableStatus)

        if (!tableStatus.exists) {
          health.overall_status = "error"
          health.issues.push(`Table '${tableName}' does not exist`)
        } else if (!tableStatus.accessible) {
          health.overall_status = "warning"
          health.issues.push(`Table '${tableName}' exists but is not accessible`)
        }
      }

      // Determine overall status
      if (health.issues.length === 0) {
        health.overall_status = "healthy"
      } else if (health.overall_status !== "error") {
        health.overall_status = "warning"
      }

      console.log('DatabaseChecker: Final health status:', health)
    } catch (error) {
      console.error('DatabaseChecker: Unexpected error:', error)
      health.overall_status = "error"
      health.issues.push(`Unexpected error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }

    return health
  }

  private async checkTable(tableName: string): Promise<TableStatus> {
    console.log(`DatabaseChecker: Checking table ${tableName}...`)
    const status: TableStatus = {
      table_name: tableName,
      exists: false,
      row_count: 0,
      accessible: false,
    }

    try {
      // Try to query the table
      const { data, error, count } = await supabase
        .from(tableName)
        .select('*', { count: 'exact', head: true })
        .limit(1)

      console.log(`DatabaseChecker: Table ${tableName} query result:`, { data, error, count })

      if (error) {
        if (error.code === '42P01') {
          // Table doesn't exist
          console.log(`DatabaseChecker: Table ${tableName} doesn't exist`)
          status.exists = false
          status.error = "Table does not exist"
        } else if (error.code === '42501') {
          // Permission denied
          console.log(`DatabaseChecker: Table ${tableName} permission denied`)
          status.exists = true
          status.accessible = false
          status.error = "Permission denied"
        } else {
          // Other error
          console.log(`DatabaseChecker: Table ${tableName} other error:`, error.message)
          status.exists = true
          status.accessible = false
          status.error = error.message
        }
      } else {
        // Table exists and is accessible
        console.log(`DatabaseChecker: Table ${tableName} is accessible with ${count} rows`)
        status.exists = true
        status.accessible = true
        status.row_count = count || 0
      }

      // Additional check: Try to get actual row count (bypass RLS for admins)
      if (status.exists && status.accessible) {
        try {
          const { count: actualCount, error: countError } = await supabase
            .from(tableName)
            .select('*', { count: 'exact', head: true })
          
          if (!countError && actualCount !== null) {
            console.log(`DatabaseChecker: Actual count for ${tableName}: ${actualCount}`)
            status.row_count = actualCount
          }
        } catch (countErr) {
          console.log(`DatabaseChecker: Could not get actual count for ${tableName}:`, countErr)
        }
      }

    } catch (error) {
      console.error(`DatabaseChecker: Error checking table ${tableName}:`, error)
      status.error = error instanceof Error ? error.message : 'Unknown error'
    }

    console.log(`DatabaseChecker: Final status for ${tableName}:`, status)
    return status
  }

  async getTableSchema(tableName: string): Promise<any> {
    try {
      const { data, error } = await supabase
        .from(tableName)
        .select('*')
        .limit(0)

      if (error) {
        throw error
      }

      // This will give us the column information
      return data
    } catch (error) {
      console.error(`Error getting schema for ${tableName}:`, error)
      return null
    }
  }

  async testInsert(tableName: string): Promise<boolean> {
    try {
      const testData = {
        test_field: 'test_value',
        created_at: new Date().toISOString()
      }

      const { error } = await supabase
        .from(tableName)
        .insert(testData)

      if (error) {
        console.error(`Test insert failed for ${tableName}:`, error)
        return false
      }

      // Clean up test data
      await supabase
        .from(tableName)
        .delete()
        .eq('test_field', 'test_value')

      return true
    } catch (error) {
      console.error(`Test insert error for ${tableName}:`, error)
      return false
    }
  }

  async getActualTableCounts(): Promise<{ [tableName: string]: number }> {
    const counts: { [tableName: string]: number } = {}
    
    try {
      // Check if current user is admin
      const authState = authManager.getAuthState()
      if (!authState.user || authState.user.role !== 'admin') {
        console.log('DatabaseChecker: User is not admin, cannot bypass RLS')
        return counts
      }

      console.log('DatabaseChecker: Admin user detected, getting actual counts...')
      
      for (const tableName of this.requiredTables) {
        try {
          // Use raw SQL to bypass RLS for admin
          const { data, error } = await supabase
            .rpc('get_table_count', { table_name: tableName })
          
          if (error) {
            console.log(`DatabaseChecker: Error getting count for ${tableName}:`, error)
            // Fallback to regular count
            const { count } = await supabase
              .from(tableName)
              .select('*', { count: 'exact', head: true })
            counts[tableName] = count || 0
          } else {
            counts[tableName] = data || 0
          }
        } catch (err) {
          console.log(`DatabaseChecker: Exception getting count for ${tableName}:`, err)
          counts[tableName] = 0
        }
      }
    } catch (error) {
      console.error('DatabaseChecker: Error getting actual counts:', error)
    }
    
    console.log('DatabaseChecker: Actual table counts:', counts)
    return counts
  }
}

export const databaseChecker = new DatabaseChecker()
