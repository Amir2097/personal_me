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

  it('logout clears session', () => {
    const auth = useAuthStore()
    auth.setSession('user', false)
    auth.logout()
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.username).toBe('')
  })
})
