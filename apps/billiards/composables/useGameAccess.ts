/** RBAC helpers for game endpoints (sync vs personal data). */

export const SYNC_DENIED_MESSAGE =
  'Трансляция на табло доступна операторам зала. Выйдите из аккаунта игрока или попросите роль operator у администратора.'

export const useGameAccess = () => {
  const suknoAuth = useSuknoAuth()

  const canSyncRoom = computed(() => {
    if (!suknoAuth.isAccountUser.value) return true
    return suknoAuth.isOperator.value
  })

  return { canSyncRoom, syncDeniedMessage: SYNC_DENIED_MESSAGE }
}
