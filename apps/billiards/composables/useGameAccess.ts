/** RBAC helpers for game endpoints (sync vs personal data). */

import { canSyncRoomForRole } from '~/utils/suknoRoles'

export const SYNC_DENIED_MESSAGE =
  'Трансляцию на табло может вести оператор или администратор. Просмотр по ссылке /tv доступен всем без входа.'

export const useGameAccess = () => {
  const suknoAuth = useSuknoAuth()

  const canSyncRoom = computed(() => canSyncRoomForRole(suknoAuth.profile.value?.role))

  return { canSyncRoom, syncDeniedMessage: SYNC_DENIED_MESSAGE }
}
