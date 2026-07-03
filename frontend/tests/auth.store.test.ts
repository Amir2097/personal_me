import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import { useAuthStore } from '../stores/auth'

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('starts as guest', () => {
    const auth = useAuthStore()
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.username).toBe('')
  })

  it('setSession marks user authenticated', () => {
    const auth = useAuthStore()
    auth.setSession('admin', true)
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.username).toBe('admin')
    expect(auth.isAdmin).toBe(true)
  })

  it('setProfile stores display fields', () => {
    const auth = useAuthStore()
    auth.setProfile({
      username: 'nik',
      is_admin: false,
      display_name: 'Nik',
      avatar_url: 'https://example.com/a.png',
      email: 'nik@example.com'
    })
    expect(auth.displayLabel).toBe('Nik')
    expect(auth.avatarUrl).toBe('https://example.com/a.png')
    expect(auth.email).toBe('nik@example.com')
  })

  it('displayLabel falls back to username', () => {
    const auth = useAuthStore()
    auth.setSession('guest_user', false)
    expect(auth.displayLabel).toBe('guest_user')
  })

  it('setProfile stores role', () => {
    const auth = useAuthStore()
    auth.setProfile({
      username: 'nik',
      is_admin: false,
      role: 'kent',
      display_name: 'Nik'
    })
    expect(auth.role).toBe('kent')
    expect(auth.roleLabel).toBe('Кент')
  })

  it('logout clears session', () => {
    const auth = useAuthStore()
    auth.setSession('user', false)
    auth.logout()
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.username).toBe('')
  })
})
