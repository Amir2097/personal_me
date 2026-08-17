export const STORED_ROLES = ['player', 'operator', 'admin'] as const
export type SuknoRole = (typeof STORED_ROLES)[number]

const ROLE_LEVEL: Record<SuknoRole, number> = {
  player: 1,
  operator: 2,
  admin: 3
}

export function roleLevel(role: string | null | undefined): number {
  if (role && role in ROLE_LEVEL) return ROLE_LEVEL[role as SuknoRole]
  return 0
}

export function roleAtLeast(role: string | null | undefined, minimum: SuknoRole): boolean {
  return roleLevel(role) >= roleLevel(minimum)
}

/** Operator or admin may host TV sync rooms. */
export function canSyncRoomForRole(role: string | null | undefined): boolean {
  return roleAtLeast(role, 'operator')
}

export function isOperatorRole(role: string | null | undefined): boolean {
  return canSyncRoomForRole(role)
}

export function isAdminRole(role: string | null | undefined, isAdminFlag?: boolean): boolean {
  return Boolean(isAdminFlag || role === 'admin')
}

export function roleLabel(role: string | null | undefined): string {
  if (role === 'admin') return 'Администратор'
  if (role === 'operator') return 'Оператор'
  return 'Игрок'
}
