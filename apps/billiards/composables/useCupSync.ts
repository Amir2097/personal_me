import type { CupState } from '~/types/cup'
import { normalizeCupState } from '~/types/cup'
import { useHubAuth } from '~/composables/useHubAuth'

const ROOM_KEY = 'dautovtech_cup_room'
const ROLE_KEY = 'dautovtech_cup_room_role'

export type CupSyncRole = 'host' | 'follower' | null
export type CupRoomLiveStatus = 'idle' | 'live' | 'ended'

type SessionGetResponse = {
  code: string
  revision: number
  updated_at: string
  owner_username: string
  state: Record<string, unknown>
}

/**
 * Host pushes cup Pinia state; TV polls by room code.
 */
export const useCupSync = () => {
  const { apiUrl, authHeaders, ensureAuthenticated } = useHubAuth()
  const store = useCupStore()

  const roomCode = useState<string | null>('cup-room-code', () => null)
  const role = useState<CupSyncRole>('cup-room-role', () => null)
  const revision = useState<number>('cup-room-revision', () => 0)
  const syncError = useState<string>('cup-sync-error', () => '')
  const roomStatus = useState<CupRoomLiveStatus>('cup-room-status', () => 'idle')
  const applyingRemote = useState<boolean>('cup-applying-remote', () => false)

  let pushTimer: ReturnType<typeof setTimeout> | null = null
  let pollTimer: ReturnType<typeof setInterval> | null = null

  const persistMeta = () => {
    if (!import.meta.client) return
    if (roomCode.value && role.value && roomStatus.value === 'live') {
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
    const savedRole = localStorage.getItem(ROLE_KEY) as CupSyncRole
    if (code && (savedRole === 'host' || savedRole === 'follower')) {
      roomCode.value = code
      role.value = savedRole
      roomStatus.value = 'live'
    }
  }

  const stopPolling = () => {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  const clearRoom = () => {
    stopPolling()
    roomCode.value = null
    role.value = null
    revision.value = 0
    syncError.value = ''
    roomStatus.value = 'idle'
    persistMeta()
  }

  const applyRemoteState = (remote: SessionGetResponse) => {
    if (!remote.state || typeof remote.state !== 'object') return
    applyingRemote.value = true
    try {
      store.applyRemoteState(normalizeCupState(remote.state as Partial<CupState>))
      revision.value = remote.revision
    } finally {
      void nextTick(() => {
        applyingRemote.value = false
      })
    }
  }

  const pushNow = async () => {
    if (role.value !== 'host' || !roomCode.value || applyingRemote.value) return
    if (roomStatus.value !== 'live') return
    await ensureAuthenticated()
    const res = await fetch(apiUrl(`/api/v1/cup/sessions/${encodeURIComponent(roomCode.value)}`), {
      method: 'PUT',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ state: store.exportSnapshot() })
    })
    if (!res.ok) {
      syncError.value = 'Ошибка синхронизации'
      return
    }
    const data = (await res.json()) as { revision: number }
    revision.value = data.revision
  }

  const createRoom = async () => {
    syncError.value = ''
    await ensureAuthenticated()
    const res = await fetch(apiUrl('/api/v1/cup/sessions'), {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' }
    })
    if (!res.ok) {
      syncError.value = 'Не удалось создать комнату'
      return null
    }
    const data = (await res.json()) as { code: string; revision: number }
    roomCode.value = data.code
    role.value = 'host'
    revision.value = data.revision
    roomStatus.value = 'live'
    persistMeta()
    await pushNow()
    return data.code
  }

  const schedulePush = () => {
    if (role.value !== 'host' || !roomCode.value || roomStatus.value !== 'live') return
    if (applyingRemote.value) return
    if (pushTimer) clearTimeout(pushTimer)
    pushTimer = setTimeout(() => {
      void pushNow()
    }, 400)
  }

  const onLocalChange = () => {
    if (applyingRemote.value) return
    schedulePush()
  }

  const startPolling = () => {
    stopPolling()
    pollTimer = setInterval(async () => {
      if (!roomCode.value || role.value !== 'follower') return
      const res = await fetch(apiUrl(`/api/v1/cup/sessions/${encodeURIComponent(roomCode.value)}`))
      if (res.status === 404) {
        roomStatus.value = 'ended'
        clearRoom()
        return
      }
      if (!res.ok) return
      const data = (await res.json()) as SessionGetResponse
      if (data.revision !== revision.value) applyRemoteState(data)
    }, 1000)
  }

  const joinRoom = async (code: string) => {
    syncError.value = ''
    const normalized = code.trim().toUpperCase()
    const res = await fetch(apiUrl(`/api/v1/cup/sessions/${encodeURIComponent(normalized)}`))
    if (!res.ok) {
      syncError.value = 'Комната не найдена'
      return false
    }
    const data = (await res.json()) as SessionGetResponse
    roomCode.value = data.code
    role.value = 'follower'
    roomStatus.value = 'live'
    applyRemoteState(data)
    persistMeta()
    startPolling()
    return true
  }

  const resumeFollowerIfPossible = async () => {
    hydrateMeta()
    if (role.value !== 'follower' || !roomCode.value) return false
    return joinRoom(roomCode.value)
  }

  const closeRoom = async () => {
    if (role.value === 'host' && roomCode.value) {
      await ensureAuthenticated()
      await fetch(apiUrl(`/api/v1/cup/sessions/${encodeURIComponent(roomCode.value)}`), {
        method: 'DELETE',
        headers: { ...authHeaders() }
      })
    }
    clearRoom()
  }

  const tvUrl = computed(() => {
    if (!import.meta.client || !roomCode.value) return ''
    const url = new URL('/billiards/cup/tv', window.location.origin)
    url.searchParams.set('room', roomCode.value)
    return url.toString()
  })

  return {
    roomCode,
    role,
    revision,
    syncError,
    roomStatus,
    tvUrl,
    hydrateMeta,
    createRoom,
    joinRoom,
    schedulePush,
    onLocalChange,
    pushNow,
    closeRoom,
    clearRoom,
    startPolling,
    resumeFollowerIfPossible
  }
}
