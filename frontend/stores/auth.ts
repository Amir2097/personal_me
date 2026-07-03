import { defineStore } from 'pinia'

export type AuthProfile = {
  username: string
  isAdmin: boolean
  role: string
  displayName: string
  avatarUrl: string
  email: string
}

const STORAGE_KEY = 'dautovtech_profile'

const emptyProfile = (): AuthProfile => ({
  username: '',
  isAdmin: false,
  role: 'user',
  displayName: '',
  avatarUrl: '',
  email: ''
})

const loadProfile = (): AuthProfile => {
  if (typeof window === 'undefined') {
    return emptyProfile()
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return emptyProfile()
    const parsed = JSON.parse(raw) as Partial<AuthProfile> & {
      isAdmin?: boolean
      displayName?: string
      avatarUrl?: string
    }
    return {
      username: parsed.username ?? '',
      isAdmin: Boolean(parsed.isAdmin),
      role: parsed.role ?? (parsed.isAdmin ? 'admin' : 'user'),
      displayName: parsed.displayName ?? '',
      avatarUrl: parsed.avatarUrl ?? '',
      email: parsed.email ?? ''
    }
  } catch {
    return emptyProfile()
  }
}

type ProfileState = AuthProfile & {
  initialized: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): ProfileState => ({
    ...loadProfile(),
    initialized: false
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.username),
    displayLabel: (state) => state.displayName.trim() || state.username,
    roleLabel: (state) => {
      const labels: Record<string, string> = {
        user: 'Пользователь',
        admin: 'Администратор',
        kent: 'Кент',
        rodnulka: 'Роднулька',
        customer: 'Заказчик'
      }
      return labels[state.role] || state.role
    }
  },
  actions: {
    setSession(username: string, isAdmin = false, role = isAdmin ? 'admin' : 'user') {
      this.username = username
      this.isAdmin = isAdmin
      this.role = role
      this.initialized = true
      this.persistProfile()
    },
    setProfile(profile: {
      username: string
      is_admin?: boolean
      isAdmin?: boolean
      role?: string
      display_name?: string
      displayName?: string
      avatar_url?: string
      avatarUrl?: string
      email?: string | null
    }) {
      this.username = profile.username
      const isAdmin = Boolean(profile.is_admin ?? profile.isAdmin)
      this.isAdmin = isAdmin
      this.role = profile.role ?? (isAdmin ? 'admin' : 'user')
      this.displayName = (profile.display_name ?? profile.displayName ?? '').trim()
      this.avatarUrl = (profile.avatar_url ?? profile.avatarUrl ?? '').trim()
      this.email = profile.email ?? ''
      this.initialized = true
      this.persistProfile()
    },
    setAdmin(isAdmin: boolean) {
      this.isAdmin = isAdmin
      this.persistProfile()
    },
    markInitialized() {
      this.initialized = true
    },
    logout() {
      Object.assign(this, { ...emptyProfile(), initialized: true })
      this.persistProfile()
    },
    persistProfile() {
      if (typeof window === 'undefined') return
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          username: this.username,
          isAdmin: this.isAdmin,
          role: this.role,
          displayName: this.displayName,
          avatarUrl: this.avatarUrl,
          email: this.email
        })
      )
    }
  }
})
