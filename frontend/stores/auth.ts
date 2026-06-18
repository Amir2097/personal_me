import { defineStore } from 'pinia'

const STORAGE_KEY = 'personal_me_profile'

type ProfileState = {
  username: string
  isAdmin: boolean
  initialized: boolean
}

const loadProfile = (): Pick<ProfileState, 'username' | 'isAdmin'> => {
  if (typeof window === 'undefined') {
    return { username: '', isAdmin: false }
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { username: '', isAdmin: false }
    const parsed = JSON.parse(raw) as { username?: string; isAdmin?: boolean }
    return {
      username: parsed.username ?? '',
      isAdmin: Boolean(parsed.isAdmin)
    }
  } catch {
    return { username: '', isAdmin: false }
  }
}

export const useAuthStore = defineStore('auth', {
  state: (): ProfileState => ({
    ...loadProfile(),
    initialized: false
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.username)
  },
  actions: {
    setSession(username: string, isAdmin = false) {
      this.username = username
      this.isAdmin = isAdmin
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
      this.username = ''
      this.isAdmin = false
      this.initialized = true
      this.persistProfile()
    },
    persistProfile() {
      if (typeof window === 'undefined') return
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          username: this.username,
          isAdmin: this.isAdmin
        })
      )
    }
  }
})
