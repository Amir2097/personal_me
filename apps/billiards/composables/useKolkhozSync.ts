import type { KolkhozState } from '~/types/kolkhoz'
import { normalizeState } from '~/types/kolkhoz'
import { useHubAuth } from '~/composables/useHubAuth'

const ROOM_KEY = 'dautovtech_kolkhoz_room'
const ROLE_KEY = 'dautovtech_kolkhoz_room_role'

export type SyncRole = 'host' | 'follower' | null

type SessionGetResponse = {
  code: string
  revision: number
  updated_at: string
  owner_username: string
  state: Record<string, unknown>
}

type SessionCreateResponse = {
  code: string
  revision: number
}

/**
 * Multi-device sync: host pushes Pinia state; TV polls by room code.
 */
export const useKolkhozSync = () => {
  const { apiUrl, authHeaders, username, ensureAuthenticated } = useHubAuth()
  const store = useKolkhozStore()

  const roomCode = useState<string | null>('kolkhoz-room-code', () => null)
  const role = useState<SyncRole>('kolkhoz-room-role', () => null)
  const revision = useState<number>('kolkhoz-room-revision', () => 0)
  const syncError = useState<string>('kolkhoz-sync-error', () => '')
  const lastPushedAt = useState<string | null>('kolkhoz-last-pushed', () => null)
  const applyingRemote = useState<boolean>('kolkhoz-applying-remote', () => false)

  let pushTimer: ReturnType<typeof setTimeout> | null = null
  let pollTimer: ReturnType<typeof setInterval> | null = null

  const persistMeta = () => {
    if (!import.meta.client) return
    if (roomCode.value && role.value) {
      localStorage.setItem(ROOM_KEY, roomCode.value)
      localStorage.setItem(ROLE_KEY, role.value)
    } else {
      localStorage.removeItem(ROOM_KEY)
      localStorage.removeItem(ROLE_KEY)
    }
  }

  const hydrateMeta = () => {
    if (!import.meta.client) return
    const code = localStorage.getItem(ROOM_KEY)
    const savedRole = localStorage.getItem(ROLE_KEY) as SyncRole
    if (code && (savedRole === 'host' || savedRole === 'follower')) {
      roomCode.value = code
      role.value = savedRole
    }
  }

  const clearRoom = () => {
    stopPolling()
    roomCode.value = null
    role.value = null
    revision.value = 0
    syncError.value = ''
    persistMeta()
  }

  const createRoom = async () => {
    syncError.value = ''
    const ok = await ensureAuthenticated()
    if (!ok) {
      syncError.value = 'Нужна авторизация на хабе, чтобы открыть синк.'
      return null
    }
    try {
      const created = await $fetch<SessionCreateResponse>(apiUrl('/api/v1/kolkhoz/sessions'), {
        method: 'POST',
        credentials: 'include',
        headers: authHeaders()
      })
      roomCode.value = created.code
      role.value = 'host'
      revision.value = created.revision
      persistMeta()
      await pushNow()
      return created.code
    } catch (error) {
      syncError.value = error instanceof Error ? error.message : 'Не удалось создать комнату'
      return null
    }
  }

  const joinRoom = async (code: string) => {
    syncError.value = ''
    const normalized = code.trim().toUpperCase()
    if (normalized.length < 4) {
      syncError.value = 'Введите код комнаты'
      return false
    }
    try {
      const remote = await $fetch<SessionGetResponse>(
        apiUrl(`/api/v1/kolkhoz/sessions/${encodeURIComponent(normalized)}`)
      )
      roomCode.value = remote.code
      role.value = 'follower'
      revision.value = remote.revision
      persistMeta()
      applyRemoteState(remote)
      startPolling()
      return true
    } catch {
      syncError.value = 'Комната не найдена'
      return false
    }
  }

  const applyRemoteState = (remote: SessionGetResponse) => {
    if (!remote.state || typeof remote.state !== 'object') return
    if ((remote.state as { version?: number }).version !== 1 && Object.keys(remote.state).length === 0) {
      return
    }
    applyingRemote.value = true
    try {
      const normalized = normalizeState(remote.state as Partial<KolkhozState>)
      Object.assign(store, normalized)
      if (import.meta.client) {
        localStorage.setItem('dautovtech_kolkhoz_v1', JSON.stringify({ ...store.$state }))
      }
      revision.value = remote.revision
    } finally {
      void nextTick(() => {
        applyingRemote.value = false
      })
    }
  }

  const pushNow = async () => {
    if (role.value !== 'host' || !roomCode.value) return
    if (applyingRemote.value) return
    try {
      const result = await $fetch<{ revision: number; updated_at: string }>(
        apiUrl(`/api/v1/kolkhoz/sessions/${encodeURIComponent(roomCode.value)}`),
        {
          method: 'PUT',
          credentials: 'include',
          headers: authHeaders(),
          body: {
            state: { ...store.$state },
            base_revision: revision.value
          }
        }
      )
      revision.value = result.revision
      lastPushedAt.value = result.updated_at
      syncError.value = ''
    } catch (error) {
      syncError.value = error instanceof Error ? error.message : 'Ошибка синхронизации'
    }
  }

  const schedulePush = () => {
    if (role.value !== 'host' || !roomCode.value) return
    if (applyingRemote.value) return
    if (pushTimer) clearTimeout(pushTimer)
    pushTimer = setTimeout(() => {
      void pushNow()
    }, 350)
  }

  const pollOnce = async () => {
    if (role.value !== 'follower' || !roomCode.value) return
    try {
      const remote = await $fetch<SessionGetResponse>(
        apiUrl(`/api/v1/kolkhoz/sessions/${encodeURIComponent(roomCode.value)}`)
      )
      if (remote.revision !== revision.value) {
        applyRemoteState(remote)
      }
      syncError.value = ''
    } catch {
      syncError.value = 'Нет связи с комнатой'
    }
  }

  const startPolling = (intervalMs = 1000) => {
    stopPolling()
    if (!import.meta.client) return
    pollTimer = setInterval(() => {
      void pollOnce()
    }, intervalMs)
  }

  const stopPolling = () => {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  const onLocalChange = () => {
    if (applyingRemote.value) return
    schedulePush()
  }

  const tvUrl = computed(() => {
    if (!import.meta.client || !roomCode.value) return ''
    const url = new URL('/billiards/tv', window.location.origin)
    url.searchParams.set('room', roomCode.value)
    return url.toString()
  })

  return {
    roomCode,
    role,
    revision,
    syncError,
    lastPushedAt,
    username,
    tvUrl,
    hydrateMeta,
    createRoom,
    joinRoom,
    clearRoom,
    pushNow,
    schedulePush,
    startPolling,
    stopPolling,
    onLocalChange,
    pollOnce
  }
}
