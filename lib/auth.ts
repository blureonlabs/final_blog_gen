import { supabase, type Database } from "./supabase"
import { supabaseLogger } from "./supabase-logging"

export type User = Database['public']['Tables']['users']['Row'] & {
  subscription: {
    plan: "free" | "starter" | "professional" | "enterprise"
    expires_at?: string
    payment_method?: string
  }
  role: "user" | "admin" | "moderator"
  is_active: boolean
  api_usage_limit: number
  api_usage_current: number
  last_login?: string
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

class AuthManager {
  private authState: AuthState = {
    user: null,
    isAuthenticated: false,
    isLoading: true,
  }

  private listeners: ((state: AuthState) => void)[] = []

  constructor() {
    this.initializeAuth()
  }

  private async initializeAuth() {
    try {
      // Check if Supabase is configured
      if (!supabase || !process.env.NEXT_PUBLIC_SUPABASE_URL) {
        console.warn('Supabase not configured, using mock authentication')
        // Create a mock user for development
        this.authState = {
          user: {
            id: 'mock-user-id',
            email: 'demo@example.com',
            full_name: 'Demo User',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            subscription: {
              plan: "free"
            },
            role: "user",
            is_active: true,
            api_usage_limit: 100,
            api_usage_current: 0
          },
          isAuthenticated: true,
          isLoading: false,
        }
        this.notifyListeners()
        return
      }
      
      // Get initial session
      const { data: { session } } = await supabase.auth.getSession()
      
      if (session?.user) {
        await this.loadUserProfile(session.user.id)
      } else {
        this.authState.isLoading = false
        this.notifyListeners()
      }

      // Listen for auth changes
      supabase.auth.onAuthStateChange(async (event, session) => {
        if (event === 'SIGNED_IN' && session?.user) {
          await this.loadUserProfile(session.user.id)
        } else if (event === 'SIGNED_OUT') {
          this.authState = {
            user: null,
            isAuthenticated: false,
            isLoading: false,
          }
          this.notifyListeners()
        }
      })
    } catch (error) {
      console.error('Error initializing auth:', error)
      this.authState.isLoading = false
      this.notifyListeners()
    }
  }

  private async loadUserProfile(userId: string) {
    try {
      // Check if Supabase is configured
      if (!supabase || !process.env.NEXT_PUBLIC_SUPABASE_URL) {
        console.warn('Supabase not configured, cannot load user profile')
        return
      }
      
      console.log('Loading user profile for ID:', userId)
      
      // Force refresh by not using cache
      const { data: userProfile, error } = await supabase
        .from('users')
        .select('*')
        .eq('id', userId)
        .single()

      console.log('Database query result:', { userProfile, error })

      if (error) {
        if (error.code === 'PGRST116') {
          // No rows returned - user profile doesn't exist
          console.log('No user profile found, creating new one...')
        } else {
          console.error('Database query error:', error)
          throw error
        }
      }

      if (userProfile) {
        // User profile exists, load it
        console.log('User profile found:', userProfile)
        console.log('User role:', userProfile.role)
        
        this.authState = {
          user: {
            ...userProfile,
            subscription: {
              plan: userProfile.subscription_plan || "free",
            }
          },
          isAuthenticated: true,
          isLoading: false,
        }
      } else {
        // User profile doesn't exist, create one
        console.log('Creating new user profile...')
        
        // First get the auth user to get email
        const { data: { user: authUser } } = await supabase.auth.getUser()
        
        if (!authUser) {
          throw new Error('No auth user found')
        }

        console.log('Auth user data:', authUser)

        const { data: newProfile, error: createError } = await supabase
          .from('users')
          .insert({
            id: userId,
            email: authUser.email || '',
            full_name: authUser.user_metadata?.full_name || 'New User',
            role: 'user', // Default role
          })
          .select()
          .single()

        console.log('Profile creation result:', { newProfile, createError })

        if (createError) {
          console.error('Error creating user profile:', createError)
          // Even if profile creation fails, we can still authenticate
          // Create a minimal user object from auth data
          this.authState = {
            user: {
              id: userId,
              email: authUser.email || '',
              full_name: authUser.user_metadata?.full_name || 'New User',
              role: 'user',
              is_active: true,
              api_usage_limit: 100,
              api_usage_current: 0,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              subscription: {
                plan: "free",
              }
            },
            isAuthenticated: true,
            isLoading: false,
          }
        } else {
          this.authState = {
            user: {
              ...newProfile,
              subscription: {
                plan: newProfile.subscription_plan || "free",
              }
            },
            isAuthenticated: true,
            isLoading: false,
          }
        }
      }

      console.log('Final auth state:', this.authState)
      this.notifyListeners()
    } catch (error) {
      console.error('Error loading user profile:', error)
      // Try to get basic auth user info as fallback
      try {
        const { data: { user: authUser } } = await supabase.auth.getUser()
        if (authUser) {
          this.authState = {
            user: {
              id: authUser.id,
              email: authUser.email || '',
              full_name: authUser.user_metadata?.full_name || 'New User',
              role: 'user',
              is_active: true,
              api_usage_limit: 100,
              api_usage_current: 0,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              subscription: {
                plan: "free",
              }
            },
            isAuthenticated: true,
            isLoading: false,
          }
        } else {
          this.authState.isLoading = false
        }
      } catch (fallbackError) {
        console.error('Fallback auth failed:', fallbackError)
        this.authState.isLoading = false
      }
      this.notifyListeners()
    }
  }

  private notifyListeners() {
    this.listeners.forEach((listener) => listener(this.authState))
  }

  subscribe(listener: (state: AuthState) => void) {
    this.listeners.push(listener)
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener)
    }
  }

  getAuthState(): AuthState {
    return this.authState
  }

  async signIn(email: string, password: string): Promise<{ success: boolean; error?: string }> {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) {
        return { success: false, error: error.message }
      }

      if (data.user) {
        await this.loadUserProfile(data.user.id)
        supabaseLogger.info("user", "User signed in", { user_id: data.user.id, details: `Email: ${email}` })
        return { success: true }
      }

      return { success: false, error: "Sign in failed" }
    } catch (error) {
      supabaseLogger.error("user", "Sign in failed", { details: error instanceof Error ? error.message : "Unknown error" })
      return { success: false, error: "Sign in failed. Please try again." }
    }
  }

  async signUp(email: string, password: string, name: string): Promise<{ success: boolean; error?: string }> {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: name,
          }
        }
      })

      if (error) {
        return { success: false, error: error.message }
      }

      if (data.user) {
        // Create user profile
        const { error: profileError } = await supabase
          .from('users')
          .insert({
            id: data.user.id,
            email: email,
            full_name: name,
          })

        if (profileError) {
          console.error('Error creating user profile:', profileError)
        }

        await this.loadUserProfile(data.user.id)
        supabaseLogger.info("user", "User signed up", { user_id: data.user.id, details: `Email: ${email}, Name: ${name}` })
        return { success: true }
      }

      return { success: false, error: "Sign up failed" }
    } catch (error) {
      supabaseLogger.error("user", "Sign up failed", { details: error instanceof Error ? error.message : "Unknown error" })
      return { success: false, error: "Sign up failed. Please try again." }
    }
  }

  async signOut(): Promise<void> {
    try {
      const userId = this.authState.user?.id
      
      const { error } = await supabase.auth.signOut()
      if (error) {
        console.error('Error signing out:', error)
      }

      this.authState = {
        user: null,
        isAuthenticated: false,
        isLoading: false,
      }

      this.notifyListeners()
      supabaseLogger.info("user", "User signed out", { user_id: userId })
    } catch (error) {
      console.error('Error during sign out:', error)
    }
  }

  async refreshUserProfile(): Promise<{ success: boolean; error?: string }> {
    try {
      const currentUser = this.authState.user
      if (!currentUser) {
        return { success: false, error: "No user to refresh" }
      }

      console.log('Force refreshing user profile for:', currentUser.email)
      
      // Force reload from database
      await this.loadUserProfile(currentUser.id)
      
      return { success: true }
    } catch (error) {
      console.error('Error refreshing user profile:', error)
      return { success: false, error: "Failed to refresh profile" }
    }
  }

  async updateProfile(updates: { full_name?: string }): Promise<{ success: boolean; error?: string }> {
    if (!this.authState.user) {
      return { success: false, error: "User not authenticated" }
    }

    try {
      const { error } = await supabase
        .from('users')
        .update({
          ...updates,
          updated_at: new Date().toISOString(),
        })
        .eq('id', this.authState.user.id)

      if (error) {
        throw error
      }

      // Update local state
      this.authState = {
        ...this.authState,
        user: {
          ...this.authState.user,
          ...updates,
        },
      }

      this.notifyListeners()

      supabaseLogger.success("user", "Profile updated", {
        user_id: this.authState.user?.id || 'unknown',
        details: `Updated: ${Object.keys(updates).join(', ')}`,
      })

      return { success: true }
    } catch (error) {
      supabaseLogger.error("user", "Profile update failed", {
        user_id: this.authState.user?.id || 'unknown',
        details: error instanceof Error ? error.message : "Unknown error",
      })
      return { success: false, error: "Failed to update profile. Please try again." }
    }
  }

  async updateSubscription(
    plan: User["subscription"]["plan"],
    paymentMethod?: string,
  ): Promise<{ success: boolean; error?: string }> {
    if (!this.authState.user) {
      return { success: false, error: "User not authenticated" }
    }

    try {
      // In a real app, you'd integrate with a payment processor here
      // For now, we'll simulate the subscription update
      await new Promise((resolve) => setTimeout(resolve, 1000))

      const expiresAt = new Date()
      expiresAt.setMonth(expiresAt.getMonth() + 1)

      // Update user subscription in database
      const { error } = await supabase
        .from('users')
        .update({
          subscription_plan: plan,
          subscription_expires_at: plan !== "free" ? expiresAt.toISOString() : null,
          updated_at: new Date().toISOString(),
        })
        .eq('id', this.authState.user.id)

      if (error) {
        throw error
      }

      // Update local state
      this.authState = {
        ...this.authState,
        user: {
          ...this.authState.user!,
          subscription: {
            plan,
            expires_at: plan !== "free" ? expiresAt.toISOString() : undefined,
            payment_method: paymentMethod,
          },
        },
      }

      this.notifyListeners()

      supabaseLogger.success("user", "Subscription updated", {
        user_id: this.authState.user?.id || 'unknown',
        details: `Upgraded to ${plan} plan using ${paymentMethod}`,
      })

      return { success: true }
    } catch (error) {
      supabaseLogger.error("user", "Subscription update failed", {
        user_id: this.authState.user?.id || 'unknown',
        details: error instanceof Error ? error.message : "Unknown error",
      })
      return { success: false, error: "Payment failed. Please try again." }
    }
  }

  async checkDatabaseConnection(): Promise<{ success: boolean; error?: string }> {
    try {
      // Test if we can connect to the database
      const { data, error } = await supabase
        .from('users')
        .select('count')
        .limit(1)

      if (error) {
        return { success: false, error: `Database connection failed: ${error.message}` }
      }

      return { success: true }
    } catch (error) {
      return { success: false, error: `Database check failed: ${error instanceof Error ? error.message : 'Unknown error'}` }
    }
  }

  async resetPassword(email: string): Promise<{ success: boolean; error?: string }> {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      })

      if (error) {
        return { success: false, error: error.message }
      }

      return { success: true }
    } catch (error) {
      return { success: false, error: "Password reset failed. Please try again." }
    }
  }
}

// Export singleton instance
export const authManager = new AuthManager()
