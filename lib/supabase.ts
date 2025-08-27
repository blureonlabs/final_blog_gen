import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder_anon_key_here'

// Check if we have real Supabase credentials
const hasRealCredentials = process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!hasRealCredentials) {
  console.warn('⚠️  Supabase environment variables not configured. Using placeholder client. Some features may not work.')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export const isSupabaseConfigured = () => {
  return hasRealCredentials
}

// Mock data for development when Supabase is not configured
export const getMockUserData = () => {
  if (hasRealCredentials) return null
  
  return {
    id: 'mock-user-id',
    email: 'demo@example.com',
    full_name: 'Demo User',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
}

// Database types for TypeScript
export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          email: string
          full_name: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          email: string
          full_name: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          full_name?: string
          created_at?: string
          updated_at?: string
        }
      }
      projects: {
        Row: {
          id: string
          user_id: string
          name: string
          description: string
          num_blogs: number
          completed_blogs: number
          status: 'in_progress' | 'completed' | 'failed'
          wordpress_account: string
          api_keys: {
            openai: string
            gemini: string
            serp: string
          }
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          name: string
          description: string
          num_blogs: number
          completed_blogs?: number
          status?: 'in_progress' | 'completed' | 'failed'
          wordpress_account: string
          api_keys: {
            openai: string
            gemini: string
            serp: string
          }
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          name?: string
          description?: string
          num_blogs?: number
          completed_blogs?: number
          status?: 'in_progress' | 'completed' | 'failed'
          wordpress_account?: string
          api_keys?: {
            openai: string
            gemini: string
            serp: string
          }
          created_at?: string
          updated_at?: string
        }
      }
      blogs: {
        Row: {
          id: string
          project_id: string
          title: string
          status: 'generating' | 'draft' | 'publishing' | 'published' | 'failed'
          word_count: number
          content?: string
          created_at: string
          published_at?: string
        }
        Insert: {
          id?: string
          project_id: string
          title: string
          status?: 'generating' | 'draft' | 'publishing' | 'published' | 'failed'
          word_count: number
          content?: string
          created_at?: string
          published_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          title?: string
          status?: 'generating' | 'draft' | 'publishing' | 'published' | 'failed'
          word_count?: number
          content?: string
          created_at?: string
          published_at?: string
        }
      }
    }
  }
}
