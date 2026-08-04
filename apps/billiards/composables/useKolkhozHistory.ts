import type { KolkhozState } from '~/types/kolkhoz'
import { normalizeState } from '~/types/kolkhoz'
import { useHubAuth } from '~/composables/useHubAuth'

export type GameSummary = {
  id: number
  title: string
  mode: string
  tournament_kind: string
  player_count: number
  event_count: number
  bank_total: number
  created_at: string
  updated_at: string
}

export type GameDetail = GameSummary & {
  state: Record<string, unknown>
  owner_username: string
}

export const useKolkhozHistory = () => {
  const { apiUrl, authHeaders, ensureAuthenticated } = useHubAuth()
  const store = useKolkhozStore()

  const games = useState<GameSummary[]>('kolkhoz-history-games', () => [])
  const loading = useState<boolean>('kolkhoz-history-loading', () => false)
  const error = useState<string>('kolkhoz-history-error', () => '')
  const saving = useState<boolean>('kolkhoz-history-saving', () => false)
  const lastSavedTitle = useState<string>('kolkhoz-history-last-title', () => '')

  const refresh = async () => {
    error.value = ''
    const ok = await ensureAuthenticated()
    if (!ok) {
      games.value = []
      error.value = 'Войдите через хаб, чтобы видеть историю.'
      return
    }
    loading.value = true
    try {
      games.value = await $fetch<GameSummary[]>(apiUrl('/api/v1/kolkhoz/games'), {
        credentials: 'include',
        headers: authHeaders()
      })
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Не удалось загрузить историю'
      games.value = []
    } finally {
      loading.value = false
    }
  }

  const saveCurrent = async (title = '') => {
    error.value = ''
    const ok = await ensureAuthenticated()
    if (!ok) {
      error.value = 'Нужна авторизация, чтобы сохранить партию.'
      return null
    }
    if (!store.players.length && !store.events.length) {
      error.value = 'Нечего сохранять — добавьте игроков или сыграйте партию.'
      return null
    }
    saving.value = true
    try {
      const saved = await $fetch<GameSummary>(apiUrl('/api/v1/kolkhoz/games'), {
        method: 'POST',
        credentials: 'include',
        headers: authHeaders(),
        body: {
          title,
          state: { ...store.$state }
        }
      })
      lastSavedTitle.value = saved.title
      await refresh()
      return saved
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Ошибка сохранения'
      return null
    } finally {
      saving.value = false
    }
  }

  const loadGame = async (gameId: number) => {
    error.value = ''
    const ok = await ensureAuthenticated()
    if (!ok) {
      error.value = 'Нужна авторизация.'
      return false
    }
    try {
      const detail = await $fetch<GameDetail>(apiUrl(`/api/v1/kolkhoz/games/${gameId}`), {
        credentials: 'include',
        headers: authHeaders()
      })
      const normalized = normalizeState(detail.state as Partial<KolkhozState>)
      Object.assign(store, normalized)
      store.persist()
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Не удалось загрузить партию'
      return false
    }
  }

  const removeGame = async (gameId: number) => {
    error.value = ''
    try {
      await $fetch(apiUrl(`/api/v1/kolkhoz/games/${gameId}`), {
        method: 'DELETE',
        credentials: 'include',
        headers: authHeaders()
      })
      games.value = games.value.filter((item) => item.id !== gameId)
      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Не удалось удалить'
      return false
    }
  }

  const modeLabelRu = (item: GameSummary) => {
    if (item.mode === 'casual') return 'Быстрый стол'
    if (item.tournament_kind === 'organizer') return 'Организаторская'
    if (item.tournament_kind === 'detailed') return 'Подробная'
    return 'Турнир'
  }

  return {
    games,
    loading,
    error,
    saving,
    lastSavedTitle,
    refresh,
    saveCurrent,
    loadGame,
    removeGame,
    modeLabelRu
  }
}
