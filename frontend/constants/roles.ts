export const USER_ROLES = [
  { id: 'user', label: 'Пользователь' },
  { id: 'admin', label: 'Администратор' },
  { id: 'kent', label: 'Кент' },
  { id: 'rodnulka', label: 'Роднулька' },
  { id: 'customer', label: 'Заказчик' }
] as const

export type StoredUserRole = (typeof USER_ROLES)[number]['id']

export const ROLE_LABELS: Record<StoredUserRole, string> = Object.fromEntries(
  USER_ROLES.map((role) => [role.id, role.label])
) as Record<StoredUserRole, string>

export const roleLabel = (role: string) => ROLE_LABELS[role as StoredUserRole] || role
