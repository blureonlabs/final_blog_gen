import { supabase } from "./supabase"
import { authManager } from "./auth"
import { supabaseLogger } from "./supabase-logging"

export interface Project {
  id: string
  name: string
  description: string
  num_blogs: number  // Changed from total_blogs to match database
  completed_blogs: number
  status: "pending" | "in_progress" | "partial" | "completed" | "failed" | "ready"
  wordpress_account_id?: string  // Changed from wordpress_account to match database
  api_keys?: any
  settings?: any
  // AI Model Configuration - using draft_creation_model from database
  draft_creation_model?: "openai" | "gemini"  // Single model selection
  // SerpAPI Research Configuration
  serp_api_on?: boolean
  serp_api_contents?: string | null
  enhanced_research?: boolean  // Enable enhanced research features
  // Image Generation Configuration
  generate_images?: boolean
  num_images_per_blog?: number
  created_at: string
  updated_at: string
  blogs?: Array<{
    id: string
    status: string
    project_id: string
  }>
}

export interface WordPressAccount {
  id: string
  name: string
  site_url: string
  username: string
  password: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface APIKey {
  id: string
  name: string
  service: "openai" | "gemini" | "serp" | "fal" | "other"
  api_key: string
  is_default: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserData {
  projects: Project[]
  wordpressAccounts: WordPressAccount[]
  apiKeys: APIKey[]
  usage: {
    blogs_generated: number
    blogs_limit: number
    wordpress_accounts_used: number
    wordpress_accounts_limit: number
  }
  subscription: {
    plan: "free" | "starter" | "professional" | "enterprise" | "internal"
    expires_at?: string
  }
  userFeatures?: {
    features_enabled: {
      blog_generation: boolean
      wordpress_accounts: boolean
      ai_image_generation: boolean
      advanced_features: boolean
    }
    feature_limits: {
      blogs_limit: number
      wordpress_accounts_limit: number
      images_limit: number
    }
    pricing_tier: string
  }
}

class SupabaseAPI {
  private isSupabaseConfigured(): boolean {
    return !!(supabase && process.env.NEXT_PUBLIC_SUPABASE_URL)
  }

  private getCurrentUserId(): string {
    try {
    const user = authManager.getAuthState().user
      if (!user) {
        // If no user is authenticated, return a mock user ID for development
        console.warn('No authenticated user, using mock user ID for development')
        return 'mock-user-id'
      }
    return user.id
    } catch (error) {
      console.warn('Error getting current user ID, using mock user ID:', error)
      // Return mock user ID as fallback, never throw
      return 'mock-user-id'
    }
  }

  // WordPress Accounts
  async addWordPressAccount(account: Omit<WordPressAccount, "id" | "created_at" | "updated_at" | "is_active">): Promise<WordPressAccount> {
    try {
    const userId = this.getCurrentUserId()
    
      // Check if Supabase is configured
      if (!this.isSupabaseConfigured()) {
        console.warn('Supabase not configured, cannot add WordPress account')
        throw new Error('Supabase not configured')
      }
      
      const { data, error } = await supabase
        .from('wordpress_accounts')
        .insert({
          user_id: userId,
          name: account.name,
          site_url: account.site_url,
          username: account.username,
          password: account.password,
          is_active: true
        })
        .select()
        .single()

      if (error) throw error

      // Log successful WordPress account addition (with error handling)
      try {
      await supabaseLogger.success("user", "WordPress account added successfully", {
        details: {
          account_name: account.name,
          site_url: account.site_url,
          account_id: data.id
        }
      })
      } catch (logError) {
        console.warn('Failed to log WordPress account addition:', logError)
        // Don't throw error for logging failures
      }

      return data
    } catch (error) {
      // Log failed WordPress account addition (with error handling)
      try {
      await supabaseLogger.error("user", "Failed to add WordPress account", {
        details: {
          account_name: account.name,
          site_url: account.site_url,
          error: error instanceof Error ? error.message : String(error)
        }
      })
      } catch (logError) {
        console.warn('Failed to log WordPress account addition error:', logError)
        // Don't throw error for logging failures
      }
      throw error
    }
  }

  async updateWordPressAccount(id: string, updates: Partial<WordPressAccount>): Promise<void> {
    // Add timeout wrapper to prevent hanging
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error('WordPress account update timed out after 10 seconds')), 10000)
    })

    const updatePromise = this._updateWordPressAccount(id, updates)
    
    return Promise.race([updatePromise, timeoutPromise])
  }

  private async _updateWordPressAccount(id: string, updates: Partial<WordPressAccount>): Promise<void> {
    try {
      console.log('🔄 Starting WordPress account update for ID:', id)
      console.log('🔄 Updates to apply:', updates)
      
      const userId = this.getCurrentUserId()
      console.log('🔄 Got user ID:', userId)
      
      // Check if Supabase is configured
      if (!this.isSupabaseConfigured()) {
        console.warn('Supabase not configured, cannot update WordPress account')
        throw new Error('Supabase not configured')
      }
      
      console.log('🔄 Getting current account details...')
      // Get current account details for logging
      const { data: currentAccount } = await supabase
        .from('wordpress_accounts')
        .select('name, site_url, username')
        .eq('id', id)
        .eq('user_id', userId)
        .single()
      
      console.log('🔄 Current account details:', currentAccount)
      console.log('🔄 Updating WordPress account...')

      const { error } = await supabase
        .from('wordpress_accounts')
        .update(updates)
        .eq('id', id)
        .eq('user_id', userId)

      if (error) throw error

      // Prepare logging data with NEW values being applied
      const logData: any = {
        account_name: updates.name || currentAccount?.name || 'Unknown',
        site_url: updates.site_url || currentAccount?.site_url || 'Unknown',
        username: updates.username || currentAccount?.username || 'Unknown'
      }

      console.log('✅ WordPress account updated successfully:', logData)

      // Log the activity using the existing supabaseLogger pattern
      this.logActivity('wordpress_account_updated', logData).catch(logError => {
        // Don't let logging errors affect the main operation
        console.warn('Failed to log activity (non-critical):', logError)
      })

    } catch (error) {
      console.error('❌ Failed to update WordPress account:', error)
      
      // Log the error activity (non-blocking)
      this.logActivity('wordpress_account_update_failed', {
        account_id: id,
        error: error instanceof Error ? error.message : String(error)
      }).catch(logError => {
        console.warn('Failed to log error activity (non-critical):', logError)
      })
      
      throw error
    }
  }

  // Simple activity logging that won't hang
  private async logActivity(action: string, details: any): Promise<void> {
    try {
      // Log to console for immediate visibility
      console.log(`📝 Activity Log [${action}]:`, details)
      
      // Use the existing supabaseLogger pattern (non-blocking)
      if (this.isSupabaseConfigured()) {
        await supabaseLogger.info("user", action, { details })
      }
      
    } catch (error) {
      // Logging failures should never break the main functionality
      console.warn('Activity logging failed (non-critical):', error)
    }
  }

  async deleteWordPressAccount(id: string): Promise<void> {
    try {
    const userId = this.getCurrentUserId()
    
      // Check if Supabase is configured
      if (!this.isSupabaseConfigured()) {
        console.warn('Supabase not configured, cannot delete WordPress account')
        throw new Error('Supabase not configured')
      }
      
      // Get account details for logging before deletion
      const { data: accountToDelete } = await supabase
        .from('wordpress_accounts')
        .select('name, site_url')
        .eq('id', id)
        .eq('user_id', userId)
        .single()

      const { error } = await supabase
        .from('wordpress_accounts')
        .delete()
        .eq('id', id)
        .eq('user_id', userId)

      if (error) throw error

      // Log successful WordPress account deletion (with error handling)
      try {
      await supabaseLogger.warning("user", "WordPress account deleted", {
        details: {
          account_id: id,
          account_name: accountToDelete?.name || 'Unknown',
          site_url: accountToDelete?.site_url || 'Unknown'
        }
      })
      } catch (logError) {
        console.warn('Failed to log WordPress account deletion:', logError)
        // Don't throw error for logging failures
      }
    } catch (error) {
      // Log failed WordPress account deletion (with error handling)
      try {
      await supabaseLogger.error("user", "Failed to delete WordPress account", {
        details: {
          account_id: id,
          error: error instanceof Error ? error.message : String(error)
        }
      })
      } catch (logError) {
        console.warn('Failed to log WordPress account deletion error:', logError)
        // Don't throw error for logging failures
      }
      throw error
    }
  }

  async getWordPressAccounts(): Promise<WordPressAccount[]> {
    try {
    const userId = this.getCurrentUserId()
      
      // Check if Supabase is configured
      if (!this.isSupabaseConfigured()) {
        console.warn('Supabase not configured, returning mock WordPress accounts')
        return []
      }
    
    const { data, error } = await supabase
      .from('wordpress_accounts')
      .select('*')
      .eq('user_id', userId)
      .eq('is_active', true)
      .order('created_at', { ascending: false })

      if (error) {
        console.error("Error loading WordPress accounts:", error)
        return []
      }
      
    return data || []
    } catch (error) {
      console.error("Error in getWordPressAccounts:", error)
      return []
    }
  }

  // API Keys
  async addAPIKey(key: Omit<APIKey, "id" | "created_at" | "updated_at" | "is_active">): Promise<APIKey> {
    try {
    const userId = this.getCurrentUserId()
    
      // Check if Supabase is configured
      if (!this.isSupabaseConfigured()) {
        console.warn('Supabase not configured, cannot add API key')
        throw new Error('Supabase not configured')
      }
      
      // If this is the first key for this service, make it default
      const existingKeys = await this.getAPIKeys()
      const isDefault = existingKeys.filter(k => k.service === key.service).length === 0
      
      const { data, error } = await supabase
        .from('api_keys')
        .insert({
          user_id: userId,
          name: key.name,
          service: key.service,
          api_key: key.api_key,
          is_default: isDefault,
          is_active: true
        })
        .select()
        .single()

      if (error) throw error

      // Log successful API key addition (with error handling)
      try {
        await supabaseLogger.success("user", "API key added successfully", {
          details: {
            key_name: key.name,
            service: key.service,
            is_default: isDefault,
            key_id: data.id
          }
        })
      } catch (logError) {
        console.warn('Failed to log API key addition:', logError)
        // Don't throw error for logging failures
      }

      return data
    } catch (error) {
      // Log failed API key addition (with error handling)
      try {
      await supabaseLogger.error("user", "Failed to add API key", {
        details: {
          key_name: key.name,
          service: key.service,
          error: error instanceof Error ? error.message : String(error)
        }
      })
      } catch (logError) {
        console.warn('Failed to log API key addition error:', logError)
        // Don't throw error for logging failures
      }
      throw error
    }
  }

  async updateAPIKey(id: string, updates: Partial<APIKey>): Promise<void> {
    try {
    const userId = this.getCurrentUserId()
    
      // Check if Supabase is configured
      if (!this.isSupabaseConfigured()) {
        console.warn('Supabase not configured, cannot update API key')
        throw new Error('Supabase not configured')
      }
      
      // Get current key details for logging
      const { data: currentKey } = await supabase
        .from('api_keys')
        .select('name, service, api_key, is_default, is_active')
        .eq('id', id)
        .eq('user_id', userId)
        .single()

      const { error } = await supabase
        .from('api_keys')
        .update(updates)
        .eq('id', id)
        .eq('user_id', userId)

      if (error) throw error

      // Prepare logging data with NEW values being applied
      const logData: any = {
        key_name: updates.name || currentKey?.name || 'Unknown',
        service: currentKey?.service || 'Unknown'  // Service typically doesn't change
      }

      console.log('✅ API key updated successfully:', logData)

      // Log the activity using the same pattern
      this.logActivity('api_key_updated', logData).catch(logError => {
        // Don't let logging errors affect the main operation
        console.warn('Failed to log activity (non-critical):', logError)
      })
    } catch (error) {
      // Log failed API key update (with error handling)
      try {
      await supabaseLogger.error("user", "Failed to update API key", {
        details: {
          key_id: id,
          error: error instanceof Error ? error.message : String(error)
        }
      })
      } catch (logError) {
        console.warn('Failed to log API key update error:', logError)
        // Don't throw error for logging failures
      }
      throw error
    }
  }

  async deleteAPIKey(id: string): Promise<void> {
    try {
    const userId = this.getCurrentUserId()
    
      // Check if Supabase is configured
      if (!this.isSupabaseConfigured()) {
        console.warn('Supabase not configured, cannot delete API key')
        throw new Error('Supabase not configured')
      }
      
      // Get key details for logging before deletion
      const { data: keyToDelete } = await supabase
        .from('api_keys')
        .select('name, service')
        .eq('id', id)
        .eq('user_id', userId)
        .single()

      const { error } = await supabase
        .from('api_keys')
        .delete()
        .eq('id', id)
        .eq('user_id', userId)

      if (error) throw error

      // Log successful API key deletion (with error handling)
      try {
      await supabaseLogger.warning("user", "API key deleted", {
        details: {
          key_id: id,
          key_name: keyToDelete?.name || 'Unknown',
          service: keyToDelete?.service || 'Unknown'
        }
      })
      } catch (logError) {
        console.warn('Failed to log API key deletion:', logError)
        // Don't throw error for logging failures
      }
    } catch (error) {
      // Log failed API key deletion (with error handling)
      try {
      await supabaseLogger.error("user", "Failed to delete API key", {
        details: {
          key_id: id,
          error: error instanceof Error ? error.message : String(error)
        }
      })
      } catch (logError) {
        console.warn('Failed to log API key deletion error:', logError)
        // Don't throw error for logging failures
      }
      throw error
    }
  }

  async getAPIKeys(): Promise<APIKey[]> {
    try {
    const userId = this.getCurrentUserId()
      
      // Check if Supabase is configured
      if (!this.isSupabaseConfigured()) {
        console.warn('Supabase not configured, returning mock API keys')
        return []
      }
    
    const { data, error } = await supabase
      .from('api_keys')
      .select('*')
      .eq('user_id', userId)
      .eq('is_active', true)
      .order('created_at', { ascending: false })

      if (error) {
        console.error("Error loading API keys:", error)
        return []
      }
      
    return data || []
    } catch (error) {
      console.error("Error in getAPIKeys:", error)
      return []
    }
  }

  // Projects
  async addProject(project: Omit<Project, "id" | "created_at" | "updated_at">): Promise<Project> {
    try {
    const userId = this.getCurrentUserId()
      
      // Check if Supabase is configured
      if (!this.isSupabaseConfigured()) {
        console.warn('Supabase not configured, returning mock project for demo mode')
        // Return a mock project for demo mode instead of throwing an error
        return {
          id: `mock-project-${Date.now()}`,
          name: project.name,
          description: project.description,
          num_blogs: project.num_blogs,
          completed_blogs: 0,
          status: project.status, // Use the status passed from the modal
          wordpress_account_id: project.wordpress_account_id,
          api_keys: project.api_keys,
          settings: project.settings,
          draft_creation_model: project.draft_creation_model,
          serp_api_on: project.serp_api_on,
          serp_api_contents: project.serp_api_contents,
          generate_images: project.generate_images || false,
          num_images_per_blog: project.num_images_per_blog || 1,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      }

      // Ensure project ID is a valid UUID string
      const projectData = {
        name: project.name,
        description: project.description,
        num_blogs: project.num_blogs || 0,
        completed_blogs: project.completed_blogs || 0,
        status: project.status || 'pending',
        wordpress_account_id: project.wordpress_account_id || null,
        api_keys: project.api_keys,
        settings: project.settings,
        draft_creation_model: project.draft_creation_model || null,
        serp_api_on: project.serp_api_on || false,
        enhanced_research: project.enhanced_research || false,  // Add enhanced research field
        serp_api_contents: project.serp_api_contents || null,
        generate_images: project.generate_images || false,  // Add image generation field
        num_images_per_blog: project.num_images_per_blog || 1,  // Add number of images per blog field
        user_id: userId
      }

      console.log('🔍 Adding project to Supabase:', projectData)
      
      // Debug Supabase connection
      console.log('🔍 Supabase URL:', process.env.NEXT_PUBLIC_SUPABASE_URL)
      console.log('🔍 Supabase configured:', this.isSupabaseConfigured())
      console.log('🔍 Supabase client:', !!supabase)
      
      // Test Supabase connection first
      try {
        console.log('🔍 Testing Supabase connection...')
        const testResponse = await supabase.from('projects').select('id').limit(1)
        console.log('🔍 Supabase connection test result:', testResponse)
      } catch (testError) {
        console.error('❌ Supabase connection test failed:', testError)
        const errorMessage = testError instanceof Error ? testError.message : String(testError)
        throw new Error(`Supabase connection failed: ${errorMessage}`)
      }
      
      try {
        // Add timeout to prevent hanging
        const timeoutPromise = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Supabase operation timed out after 10 seconds')), 10000)
        })
        
        const supabasePromise = supabase
          .from('projects')
          .insert(projectData)
          .select()
          .single()
        
        const result = await Promise.race([supabasePromise, timeoutPromise]) as any
        const { data, error } = result
        
        console.log('🔍 Supabase response received:', { data, error })
        
        if (error) {
          console.error('❌ Error adding project:', error)
          
          // Check if it's a constraint violation
          if ('code' in error && error.code === '23514') {
            throw new Error(`Database constraint violation: ${error.message}. Please check your project data.`)
          } else if ('code' in error && error.code === '23505') {
            throw new Error(`Duplicate project: ${error.message}`)
          } else {
            throw new Error(`Failed to create project: ${error.message}`)
          }
        }

        console.log('✅ Project added successfully:', data)
        return data
      } catch (insertError) {
        console.error('❌ Supabase insert failed:', insertError)
        throw insertError
      }
    } catch (error) {
      console.error('❌ Error in addProject:', error)
      throw error
    }
  }

  async getProjects(): Promise<Project[]> {
    try {
    const userId = this.getCurrentUserId()
      
      // Check if Supabase is configured
      if (!this.isSupabaseConfigured()) {
        console.warn('Supabase not configured, returning mock projects')
        return []
      }
    
    const { data, error } = await supabase
      .from('projects')
      .select(`
        *,
        blogs (
          id,
          status,
          project_id,
          is_published
        )
      `)
      .eq('user_id', userId)
      .order('created_at', { ascending: false })

      if (error) {
        console.error("Error loading projects:", error)
        return []
      }
      
    return data || []
    } catch (error) {
      console.error("Error in getProjects:", error)
      return []
    }
  }

  // Get all user data
  async getUserData(): Promise<UserData> {
    try {
    const userId = this.getCurrentUserId()
    
    const [projects, wordpressAccounts, apiKeys, userProfile] = await Promise.all([
      this.getProjects(),
      this.getWordPressAccounts(),
      this.getAPIKeys(),
      this.getUserProfile()
    ])

    // Get user features and limits from database
    const features = userProfile?.features_enabled || {
      blog_generation: true,
      wordpress_accounts: false,
      ai_image_generation: false,
      advanced_features: false
    }

    const limits = userProfile?.feature_limits || {
      blogs_limit: 50,
      wordpress_accounts_limit: 10,
      images_limit: 100
    }

    const pricingTier = userProfile?.pricing_tier || 'free'

    return {
      projects,
      wordpressAccounts,
      apiKeys,
      usage: {
        blogs_generated: 0,
        blogs_limit: limits.blogs_limit,
        wordpress_accounts_used: wordpressAccounts.length,
        wordpress_accounts_limit: limits.wordpress_accounts_limit
      },
      subscription: {
        plan: pricingTier === 'internal' ? 'internal' : 'free'
      },
      userFeatures: {
        features_enabled: features,
        feature_limits: limits,
        pricing_tier: pricingTier
        }
      }
    } catch (error) {
      console.warn("Error in getUserData, returning default data:", error)
      // Return default data structure on any error
      return {
        projects: [],
        wordpressAccounts: [],
        apiKeys: [],
        usage: {
          blogs_generated: 0,
          blogs_limit: 50,
          wordpress_accounts_used: 0,
          wordpress_accounts_limit: 10
        },
        subscription: {
          plan: 'free'
        },
        userFeatures: {
          features_enabled: {
            blog_generation: true,
            wordpress_accounts: false,
            ai_image_generation: false,
            advanced_features: false
          },
          feature_limits: {
            blogs_limit: 50,
            wordpress_accounts_limit: 10,
            images_limit: 100
          },
          pricing_tier: 'free'
        }
      }
    }
  }

  // Get user profile with features
  private async getUserProfile() {
    try {
    const userId = this.getCurrentUserId()
    
      // Check if Supabase is configured
      if (!this.isSupabaseConfigured()) {
        console.warn('Supabase not configured, returning mock user profile')
        return {
          features_enabled: {
            blog_generation: true,
            wordpress_accounts: false,
            ai_image_generation: false,
            advanced_features: false
          },
          feature_limits: {
            blogs_limit: 50,
            wordpress_accounts_limit: 10,
            images_limit: 100
          },
          pricing_tier: 'free'
        }
      }
      
      // Additional safety check
      if (!supabase || !process.env.NEXT_PUBLIC_SUPABASE_URL) {
        console.warn('Supabase check failed, returning mock user profile')
        return {
          features_enabled: {
            blog_generation: true,
            wordpress_accounts: false,
            ai_image_generation: false,
            advanced_features: false
          },
          feature_limits: {
            blogs_limit: 50,
            wordpress_accounts_limit: 10,
            images_limit: 100
          },
          pricing_tier: 'free'
        }
      }
      
      try {
    const { data, error } = await supabase
      .from('users')
      .select('features_enabled, feature_limits, pricing_tier')
      .eq('id', userId)
      .single()

    if (error) {
          console.warn("Error loading user profile from Supabase:", error)
          // Return default profile on error, don't throw
          return {
            features_enabled: {
              blog_generation: true,
              wordpress_accounts: false,
              ai_image_generation: false,
              advanced_features: false
            },
            feature_limits: {
              blogs_limit: 50,
              wordpress_accounts_limit: 10,
              images_limit: 100
            },
            pricing_tier: 'free'
          }
        }

        // If we have data, return it with defaults for missing fields
        return {
          features_enabled: {
            blog_generation: true,
            wordpress_accounts: false,
            ai_image_generation: false,
            advanced_features: false,
            ...data.features_enabled
          },
          feature_limits: {
            blogs_limit: 50,
            wordpress_accounts_limit: 10,
            images_limit: 100,
            ...data.feature_limits
          },
          pricing_tier: data.pricing_tier || 'free'
        }
      } catch (supabaseError) {
        console.warn("Supabase query error in getUserProfile:", supabaseError)
        // Return default profile on any Supabase error, don't throw
        return {
          features_enabled: {
            blog_generation: true,
            wordpress_accounts: false,
            ai_image_generation: false,
            advanced_features: false
          },
          feature_limits: {
            blogs_limit: 50,
            wordpress_accounts_limit: 10,
            images_limit: 100
          },
          pricing_tier: 'free'
        }
      }
    } catch (error) {
      console.warn("Unexpected error in getUserProfile:", error)
      // Return default profile on any error, don't throw
      return {
        features_enabled: {
          blog_generation: true,
          wordpress_accounts: false,
          ai_image_generation: false,
          advanced_features: false
        },
        feature_limits: {
          blogs_limit: 50,
          wordpress_accounts_limit: 10,
          images_limit: 100
        },
        pricing_tier: 'free'
      }
    }
  }
}

export const supabaseApi = new SupabaseAPI()

