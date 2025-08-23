export interface Project {
  id: string
  name: string
  description: string
  total_blogs: number
  completed_blogs: number
  status: "in_progress" | "completed" | "failed"
  wordpress_account: string
  api_keys: {
    openai: string
    gemini: string
    serp: string
  }
  created_at: string
  updated_at: string
  blogs?: Blog[]
}

export interface Blog {
  id: string
  title: string
  status: "generating" | "draft" | "publishing" | "published" | "failed"
  word_count: number
  created_at: string
  published_at?: string
}

export interface WordPressAccount {
  id: string
  name: string
  url: string
  username: string
  password: string
}

export interface APIKey {
  id: string
  name: string
  key: string
  service: "openai" | "gemini" | "serp"
  isDefault: boolean
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
    plan: "free" | "starter" | "professional" | "enterprise"
    expires_at?: string
  }
}

const STORAGE_KEY = "bulk_blog_generator_data"

export const storage = {
  getData: (): UserData => {
    if (typeof window === "undefined") return getDefaultData()

    try {
      const data = localStorage.getItem(STORAGE_KEY)
      return data ? JSON.parse(data) : getDefaultData()
    } catch (error) {
      console.error("Error loading data from localStorage:", error)
      return getDefaultData()
    }
  },

  saveData: (data: UserData): void => {
    if (typeof window === "undefined") return

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    } catch (error) {
      console.error("Error saving data to localStorage:", error)
    }
  },

  addProject: (project: Omit<Project, "id" | "created_at" | "updated_at">): Project => {
    const data = storage.getData()
    const newProject: Project = {
      ...project,
      id: generateId(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    data.projects.push(newProject)
    storage.saveData(data)
    return newProject
  },

  updateProject: (projectId: string, updates: Partial<Project>): void => {
    const data = storage.getData()
    const projectIndex = data.projects.findIndex((p) => p.id === projectId)

    if (projectIndex !== -1) {
      data.projects[projectIndex] = {
        ...data.projects[projectIndex],
        ...updates,
        updated_at: new Date().toISOString(),
      }
      storage.saveData(data)
    }
  },

  deleteProject: (projectId: string): void => {
    const data = storage.getData()
    data.projects = data.projects.filter((p) => p.id !== projectId)
    storage.saveData(data)
  },

  addWordPressAccount: (account: Omit<WordPressAccount, "id">): WordPressAccount => {
    const data = storage.getData()
    const newAccount: WordPressAccount = {
      ...account,
      id: generateId(),
    }

    data.wordpressAccounts.push(newAccount)
    storage.saveData(data)
    return newAccount
  },

  updateWordPressAccount: (accountId: string, updates: Partial<WordPressAccount>): void => {
    const data = storage.getData()
    const accountIndex = data.wordpressAccounts.findIndex((a) => a.id === accountId)

    if (accountIndex !== -1) {
      data.wordpressAccounts[accountIndex] = {
        ...data.wordpressAccounts[accountIndex],
        ...updates,
      }
      storage.saveData(data)
    }
  },

  deleteWordPressAccount: (accountId: string): void => {
    const data = storage.getData()
    data.wordpressAccounts = data.wordpressAccounts.filter((a) => a.id !== accountId)
    storage.saveData(data)
  },

  addAPIKey: (apiKey: Omit<APIKey, "id">): APIKey => {
    const data = storage.getData()
    const newAPIKey: APIKey = {
      ...apiKey,
      id: generateId(),
    }

    // If this is set as default, remove default from other keys of same service
    if (newAPIKey.isDefault) {
      data.apiKeys.forEach((key) => {
        if (key.service === newAPIKey.service) {
          key.isDefault = false
        }
      })
    }

    data.apiKeys.push(newAPIKey)
    storage.saveData(data)
    return newAPIKey
  },

  updateAPIKey: (keyId: string, updates: Partial<APIKey>): void => {
    const data = storage.getData()
    const keyIndex = data.apiKeys.findIndex((k) => k.id === keyId)

    if (keyIndex !== -1) {
      const updatedKey = { ...data.apiKeys[keyIndex], ...updates }

      // If setting as default, remove default from other keys of same service
      if (updates.isDefault) {
        data.apiKeys.forEach((key) => {
          if (key.service === updatedKey.service && key.id !== keyId) {
            key.isDefault = false
          }
        })
      }

      data.apiKeys[keyIndex] = updatedKey
      storage.saveData(data)
    }
  },

  deleteAPIKey: (keyId: string): void => {
    const data = storage.getData()
    data.apiKeys = data.apiKeys.filter((k) => k.id !== keyId)
    storage.saveData(data)
  },

  updateUsage: (usage: Partial<UserData["usage"]>): void => {
    const data = storage.getData()
    data.usage = { ...data.usage, ...usage }
    storage.saveData(data)
  },

  updateSubscription: (subscription: Partial<UserData["subscription"]>): void => {
    const data = storage.getData()
    data.subscription = { ...data.subscription, ...subscription }
    storage.saveData(data)
  },
}

function getDefaultData(): UserData {
  return {
    projects: [],
    wordpressAccounts: [],
    apiKeys: [],
    usage: {
      blogs_generated: 0,
      blogs_limit: 10,
      wordpress_accounts_used: 0,
      wordpress_accounts_limit: 1,
    },
    subscription: {
      plan: "free",
    },
  }
}

function generateId(): string {
  return Math.random().toString(36).substr(2, 9)
}
