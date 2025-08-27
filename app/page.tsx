"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Dashboard } from "@/components/dashboard"
import { AuthForm } from "@/components/auth-form"
import { authManager, type User } from "@/lib/auth"

export default function Home() {
  const searchParams = useSearchParams()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsubscribe = authManager.subscribe((authState) => {
      console.log('Auth state changed:', authState)
      if (!authState.isLoading) {
        console.log('Setting user state to:', authState.user)
        setUser(authState.user)
        setLoading(false)
      }
    })

    // Also check current state immediately
    const currentState = authManager.getAuthState()
    console.log('Current auth state:', currentState)
    if (!currentState.isLoading) {
      console.log('Setting user state immediately to:', currentState.user)
      setUser(currentState.user)
      setLoading(false)
    }

    return unsubscribe
  }, [])

  console.log('Component render - user:', user, 'loading:', loading)

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Initializing application...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    console.log('No user, showing AuthForm')
    return <AuthForm />
  }

  console.log('User authenticated, showing Dashboard')
  return (
    <div className="min-h-screen bg-gray-100">
      <Dashboard user={user} />
    </div>
  )
}
