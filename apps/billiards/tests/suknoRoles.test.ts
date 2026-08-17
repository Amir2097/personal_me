import { describe, expect, it } from 'vitest'
import {
  canSyncRoomForRole,
  isAdminRole,
  isOperatorRole,
  roleAtLeast,
  roleLabel,
  roleLevel
} from '../utils/suknoRoles'

describe('suknoRoles', () => {
  it('orders roles by level', () => {
    expect(roleLevel('player')).toBeLessThan(roleLevel('operator'))
    expect(roleLevel('operator')).toBeLessThan(roleLevel('admin'))
    expect(roleLevel('unknown')).toBe(0)
  })

  it('checks minimum role', () => {
    expect(roleAtLeast('admin', 'operator')).toBe(true)
    expect(roleAtLeast('operator', 'operator')).toBe(true)
    expect(roleAtLeast('player', 'operator')).toBe(false)
  })

  it('allows sync only for operator and admin', () => {
    expect(canSyncRoomForRole('player')).toBe(false)
    expect(canSyncRoomForRole('operator')).toBe(true)
    expect(canSyncRoomForRole('admin')).toBe(true)
    expect(isOperatorRole('admin')).toBe(true)
  })

  it('detects admin role', () => {
    expect(isAdminRole('operator')).toBe(false)
    expect(isAdminRole('admin')).toBe(true)
    expect(isAdminRole('player', true)).toBe(true)
  })

  it('maps role labels', () => {
    expect(roleLabel('admin')).toBe('Администратор')
    expect(roleLabel('operator')).toBe('Оператор')
    expect(roleLabel('player')).toBe('Игрок')
  })
})
