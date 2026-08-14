import type { KolkhozState } from '~/types/kolkhoz'
import { normalizeState } from '~/types/kolkhoz'
import { useHubAuth } from '~/composables/useHubAuth'

const LAST_SAVED_KEY = 'dautovtech_kolkhoz_last_saved_game'

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
  const lastSavedId = useState<number | null>('kolkhoz-history-last-id', () => null)

  const hydrateLastSaved = () => {
    if (!import.meta.client) return
    const raw = localStorage.getItem(LAST_SAVED_KEY)
    if (!raw) return
    const id = Number(raw)
    if (Number.isFinite(id) && id > 0) lastSavedId.value = id
  }

  const rememberSaved = (saved: GameSummary) => {
    lastSavedId.value = saved.id
    lastSavedTitle.value = saved.title
    if (import.meta.client) localStorage.setItem(LAST_SAVED_KEY, String(saved.id))
  }

  const sessionHint = computed(() => {
    const players = store.players.length
    const eliminated = store.players.filter((p) => p.status === 'eliminated').length
    const bank = store.totalBank
    const round = store.currentRound?.number
    const buyIns = store.tournament.buyIns?.length || 0
    const parts: string[] = []
    if (store.mode === 'tournament' && round) parts.push(`тур ${round}`)
    parts.push(`игроков ${players}`)
    if (eliminated) parts.push(`выбыло ${eliminated}`)
    if (buyIns) parts.push(`взносов ${buyIns}`)
    if (bank) parts.push(`банк ${bank.toLocaleString('ru-RU')} ₽`)
    parts.push(`событий ${store.events.length}`)
    return parts.join(' · ')
  })

  const refresh = async () => {
    error.value = ''
    const ok = await ensureAuthenticated()
      if (!ok) {
        games.value = []
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

  const saveCurrent = async (title = '', { asNew = false }: { asNew?: boolean } = {}) => {
    error.value = ''
    const ok = await ensureAuthenticated()
    if (!ok) {
      error.value = 'Облако сейчас недоступно. Игра на устройстве уже сохраняется сама.'
      return null
    }
    if (!store.players.length && !store.events.length) {
      error.value = 'Нечего сохранять — добавьте игроков или сыграйте партию.'
      return null
    }
    saving.value = true
    try {
      const body = {
        title,
        state: { ...store.$state }
      }
      const shouldUpdate = !asNew && lastSavedId.value
      const saved = shouldUpdate
        ? await $fetch<GameSummary>(apiUrl(`/api/v1/kolkhoz/games/${lastSavedId.value}`), {
            method: 'PUT',
            credentials: 'include',
            headers: authHeaders(),
            body
          })
        : await $fetch<GameSummary>(apiUrl('/api/v1/kolkhoz/games'), {
            method: 'POST',
            credentials: 'include',
            headers: authHeaders(),
            body
          })
      rememberSaved(saved)
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
      rememberSaved(detail)
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
      if (lastSavedId.value === gameId) {
        lastSavedId.value = null
        lastSavedTitle.value = ''
        if (import.meta.client) localStorage.removeItem(LAST_SAVED_KEY)
      }
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
    lastSavedId,
    sessionHint,
    hydrateLastSaved,
    refresh,
    saveCurrent,
    loadGame,
    removeGame,
    modeLabelRu
  }
}
