export interface EnvironmentStatus {
  supabase_url: boolean
  supabase_anon_key: boolean
  all_configured: boolean
  missing_vars: string[]
}

export function checkEnvironment(): EnvironmentStatus {
  const status: EnvironmentStatus = {
    supabase_url: false,
    supabase_anon_key: false,
    all_configured: false,
    missing_vars: []
  }

  // Check Supabase URL
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  if (supabaseUrl && supabaseUrl !== 'https://your-project.supabase.co') {
    status.supabase_url = true
  } else {
    status.missing_vars.push('NEXT_PUBLIC_SUPABASE_URL')
  }

  // Check Supabase Anon Key
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  if (supabaseAnonKey && supabaseAnonKey !== 'your-anon-key') {
    status.supabase_anon_key = true
  } else {
    status.missing_vars.push('NEXT_PUBLIC_SUPABASE_ANON_KEY')
  }

  // Check if all required vars are configured
  status.all_configured = status.supabase_url && status.supabase_anon_key

  return status
}

export function getEnvironmentRecommendations(): string[] {
  const recommendations: string[] = []
  const status = checkEnvironment()

  if (!status.supabase_url) {
    recommendations.push("Set NEXT_PUBLIC_SUPABASE_URL in your .env.local file")
  }

  if (!status.supabase_anon_key) {
    recommendations.push("Set NEXT_PUBLIC_SUPABASE_ANON_KEY in your .env.local file")
  }

  if (status.all_configured) {
    recommendations.push("All environment variables are properly configured")
  }

  return recommendations
}
