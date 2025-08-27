import { supabase } from './supabase'

export interface LogEntry {
  user_id: string
  action: string
  level: 'success' | 'info' | 'warning' | 'error'
  category: string
  timestamp?: string
  metadata?: {
    details?: any
    [key: string]: any
  }
}

class SupabaseLogger {
  async success(category: string, action: string, options?: { details?: any; [key: string]: any }) {
    return this.log('success', category, action, options)
  }

  async info(category: string, action: string, options?: { details?: string; [key: string]: any }) {
    return this.log('info', category, action, options)
  }

  async warning(category: string, action: string, options?: { details?: any; [key: string]: any }) {
    return this.log('warning', category, action, options)
  }

  async error(category: string, action: string, options?: { details?: any; [key: string]: any }) {
    return this.log('error', category, action, options)
  }

  private async log(level: 'success' | 'info' | 'warning' | 'error', category: string, action: string, options?: { details?: any; [key: string]: any }) {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      
      if (!user) {
        console.warn('No authenticated user found for logging')
        return null
      }

      const logEntry: LogEntry = {
        user_id: user.id,
        action,
        level,
        category,
        timestamp: new Date().toISOString(),
        metadata: {
          details: options?.details || null
        }
      }

      const { data, error } = await supabase
        .from('activity_logs')
        .insert(logEntry)
        .select()
        .single()

      if (error) {
        console.error('Error logging to database:', error)
        return null
      }

      return data
    } catch (error) {
      console.error('Error in supabaseLogger:', error)
      return null
    }
  }

  async getLogs(limit: number = 100) {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      
      if (!user) {
        throw new Error('No authenticated user')
      }

      const { data, error } = await supabase
        .from('activity_logs')
        .select('*')
        .eq('user_id', user.id)
        .order('timestamp', { ascending: false })
        .limit(limit)

      if (error) {
        throw error
      }

      return data
    } catch (error) {
      console.error('Error fetching logs:', error)
      return []
    }
  }

  async exportLogs() {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      
      if (!user) {
        throw new Error('No authenticated user')
      }

      const { data, error } = await supabase
        .from('activity_logs')
        .select('*')
        .eq('user_id', user.id)
        .order('timestamp', { ascending: false })

      if (error) {
        throw error
      }

      // Convert to CSV format
      const csvContent = this.convertToCSV(data)
      return csvContent
    } catch (error) {
      console.error('Error exporting logs:', error)
      return null
    }
  }

  async clearLogs() {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      
      if (!user) {
        throw new Error('No authenticated user')
      }

      const { error } = await supabase
        .from('activity_logs')
        .delete()
        .eq('user_id', user.id)

      if (error) {
        throw error
      }

      return true
    } catch (error) {
      console.error('Error clearing logs:', error)
      return false
    }
  }

  private convertToCSV(data: any[]): string {
    if (!data || data.length === 0) {
      return ''
    }

    const headers = Object.keys(data[0])
    const csvRows = [headers.join(',')]

    for (const row of data) {
      const values = headers.map(header => {
        const value = row[header]
        if (typeof value === 'object') {
          return JSON.stringify(value)
        }
        return value
      })
      csvRows.push(values.join(','))
    }

    return csvRows.join('\n')
  }
}

export const supabaseLogger = new SupabaseLogger()
