import { describe, expect, it } from 'vitest'
import { canSyncRoomForRole } from '../utils/suknoRoles'
import { SYNC_DENIED_MESSAGE } from '../composables/useGameAccess'

describe('game access rules', () => {
  it('denies sync for players and guests', () => {
    expect(canSyncRoomForRole('player')).toBe(false)
    expect(canSyncRoomForRole(null)).toBe(false)
    expect(canSyncRoomForRole(undefined)).toBe(false)
  })

  it('allows sync for hall staff roles', () => {
    expect(canSyncRoomForRole('operator')).toBe(true)
    expect(canSyncRoomForRole('admin')).toBe(true)
  })

  it('exposes a user-facing denial message', () => {
    expect(SYNC_DENIED_MESSAGE).toMatch(/оператор/i)
    expect(SYNC_DENIED_MESSAGE).toMatch(/просмотр/i)
  })
})
