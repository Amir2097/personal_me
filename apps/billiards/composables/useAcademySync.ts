/**
 * Sync academy progress with hub account.
 * localStorage remains the offline cache; server is source of truth when signed in.
 */
export const useAcademySync = () => {
  const academy = useAcademyStore()
  const { apiUrl, authHeaders, ensureAuthenticated, username } = useHubAuth()

  const syncStatus = computed(() => academy.syncStatus)
  const syncError = computed(() => academy.syncError)
  const isSignedIn = computed(() => Boolean(username.value))

  const pullAndMerge = async () => {
    academy.syncError = ''
    const ok = await ensureAuthenticated()
    if (!ok) {
      academy.syncStatus = 'offline'
      academy.syncError = 'Войдите через хаб, чтобы синхронизировать прогресс.'
      return false
    }

    academy.syncStatus = 'syncing'
    try {
      // Push local first so other devices get offline results, then pull merged view.
      const merged = await $fetch<{ items: Array<{
        exercise_id: string
        made: number
        attempts: number
        updated_at: string
      }> }>(apiUrl('/api/v1/academy/progress'), {
        method: 'PUT',
        credentials: 'include',
        headers: authHeaders(),
        body: { items: academy.exportItems() }
      })
      academy.applyServerItems(merged.items || [])
      academy.syncStatus = 'synced'
      return true
    } catch (err) {
      academy.syncStatus = 'error'
      academy.syncError = err instanceof Error ? err.message : 'Не удалось синхронизировать прогресс'
      return false
    }
  }

  const pushOne = async (exerciseId: string) => {
    const log = academy.byExercise(exerciseId)
    if (!log) return false

    const ok = await ensureAuthenticated()
    if (!ok) {
      academy.syncStatus = 'offline'
      return false
    }

    academy.syncStatus = 'syncing'
    academy.syncError = ''
    try {
      const saved = await $fetch<{
        exercise_id: string
        made: number
        attempts: number
        updated_at: string
      }>(apiUrl(`/api/v1/academy/progress/${encodeURIComponent(exerciseId)}`), {
        method: 'PUT',
        credentials: 'include',
        headers: authHeaders(),
        body: {
          made: log.made,
          attempts: log.attempts,
          updated_at: log.updatedAt
        }
      })
      academy.applyServerItems([saved])
      academy.syncStatus = 'synced'
      return true
    } catch (err) {
      academy.syncStatus = 'error'
      academy.syncError = err instanceof Error ? err.message : 'Не удалось сохранить на сервер'
      return false
    }
  }

  return {
    syncStatus,
    syncError,
    isSignedIn,
    pullAndMerge,
    pushOne
  }
}
