import { useMemo } from "react"
import { authManager, type User } from "@/lib/auth"

export interface UserPermissions {
  canViewAdmin: boolean
  canManageUsers: boolean
  canViewAllProjects: boolean
  canViewAllLogs: boolean
  canManageSystem: boolean
  canCreateProjects: boolean
  canUseAPI: boolean
  role: User["role"]
  isAdmin: boolean
  isModerator: boolean
  isRegularUser: boolean
}

export function usePermissions(): UserPermissions {
  const authState = authManager.getAuthState()
  const user = authState.user

  return useMemo(() => {
    if (!user) {
      return {
        canViewAdmin: false,
        canManageUsers: false,
        canViewAllProjects: false,
        canViewAllLogs: false,
        canManageSystem: false,
        canCreateProjects: false,
        canUseAPI: false,
        role: "user" as const,
        isAdmin: false,
        isModerator: false,
        isRegularUser: false,
      }
    }

    const isAdmin = user.role === "admin"
    const isModerator = user.role === "moderator"
    const isRegularUser = user.role === "user"

    return {
      canViewAdmin: isAdmin || isModerator,
      canManageUsers: isAdmin,
      canViewAllProjects: isAdmin || isModerator,
      canViewAllLogs: isAdmin || isModerator,
      canManageSystem: isAdmin,
      canCreateProjects: user.is_active,
      canUseAPI: user.is_active && user.api_usage_current < user.api_usage_limit,
      role: user.role,
      isAdmin,
      isModerator,
      isRegularUser,
    }
  }, [user])
}

export function useRequireRole(requiredRole: User["role"]): boolean {
  const permissions = usePermissions()
  
  switch (requiredRole) {
    case "admin":
      return permissions.isAdmin
    case "moderator":
      return permissions.isAdmin || permissions.isModerator
    case "user":
      return true
    default:
      return false
  }
}

export function useRequirePermission(permission: keyof UserPermissions): boolean {
  const permissions = usePermissions()
  return permissions[permission]
}
