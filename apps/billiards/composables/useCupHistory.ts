import type { CupState } from '~/types/cup'
import { normalizeCupState } from '~/types/cup'
import { useHubAuth } from '~/composables/useHubAuth'

const LOCAL_HISTORY_KEY = 'dautovtech_cup_history_v1'

export type CupHistorySummary = {
  id: string | number
  title: string
  format: string
  player_count: number
  winner_name: string
  status: string
  created_at: string
  source: 'local' | 'hub'
  state?: CupState
}

type HubSummary = {
  id: number
  title: string
  format: string
  player_count: number
  winner_name: string
  status: string
  created_at: string
  updated_at: string
}

const readLocal = (): CupHistorySummary[] => {
  if (!import.meta.client) return []
  try {
    const raw = localStorage.getItem(LOCAL_HISTORY_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as CupHistorySummary[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const writeLocal = (items: CupHistorySummary[]) => {
  if (!import.meta.client) return
  localStorage.setItem(LOCAL_HISTORY_KEY, JSON.stringify(items.slice(0, 40)))
}

export const useCupHistory = () => {
  const { apiUrl, authHeaders, ensureAuthenticated, username } = useHubAuth()
  const items = useState<CupHistorySummary[]>('cup-history-items', () => [])
  const error = useState<string>('cup-history-error', () => '')
  const saving = useState<boolean>('cup-history-saving', () => false)

  const refresh = async () => {
    error.value = ''
    const local = readLocal()
    let hub: CupHistorySummary[] = []
    if (username.value) {
      try {
        await ensureAuthenticated()
        const res = await fetch(apiUrl('/api/v1/cup/tournaments?limit=40'), {
          headers: { ...authHeaders() }
        })
        if (res.ok) {
          const rows = (await res.json()) as HubSummary[]
          hub = rows.map((row) => ({
            id: row.id,
            title: row.title,
            format: row.format,
            player_count: row.player_count,
            winner_name: row.winner_name,
            status: row.status,
            created_at: row.created_at,
            source: 'hub' as const
          }))
        }
      } catch {
        /* local-only fallback */
      }
    }
    items.value = [...hub, ...local.filter((item) => item.source === 'local')]
  }

  const saveSnapshot = async (state: CupState, title?: string) => {
    saving.value = true
    error.value = ''
    try {
      const snapshot = normalizeCupState(state)
      const localEntry: CupHistorySummary = {
        id: `local_${snapshot.tournament.id || Date.now()}`,
        title: title || snapshot.tournament.name || 'Турнир',
        format: snapshot.tournament.format,
        player_count: snapshot.players.length,
        winner_name:
          snapshot.players.find((player) => player.id === snapshot.tournament.winnerId)?.name || '',
        status: snapshot.tournament.status,
        created_at: snapshot.tournament.completedAt || snapshot.tournament.createdAt || new Date().toISOString(),
        source: 'local',
        state: snapshot
      }
      const local = readLocal().filter((item) => item.id !== localEntry.id)
      local.unshift(localEntry)
      writeLocal(local)

      if (username.value) {
        await ensureAuthenticated()
        const res = await fetch(apiUrl('/api/v1/cup/tournaments'), {
          method: 'POST',
          headers: { ...authHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({ state: snapshot, title: localEntry.title })
        })
        if (!res.ok) error.value = 'Сохранено локально. Синхронизация с хабом не удалась.'
      }
      await refresh()
      return true
    } finally {
      saving.value = false
    }
  }

  const loadDetail = async (id: string | number): Promise<CupState | null> => {
    if (typeof id === 'string' && id.startsWith('local_')) {
      return readLocal().find((item) => item.id === id)?.state || null
    }
    if (!username.value) return null
    await ensureAuthenticated()
    const res = await fetch(apiUrl(`/api/v1/cup/tournaments/${id}`), {
      headers: { ...authHeaders() }
    })
    if (!res.ok) return null
    const data = (await res.json()) as { state: Partial<CupState> }
    return normalizeCupState(data.state)
  }

  return { items, error, saving, refresh, saveSnapshot, loadDetail }
}
