import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase environment variables. Please check your .env.local file.')
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export const isSupabaseConfigured = () => {
  return !!(supabaseUrl && supabaseAnonKey)
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
          total_blogs: number
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
          total_blogs: number
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
          total_blogs?: number
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
