import type { KolkhozState } from '~/types/kolkhoz'
import { createEmptyState, normalizeState } from '~/types/kolkhoz'
import { useHubAuth } from '~/composables/useHubAuth'

const ROOM_KEY = 'dautovtech_kolkhoz_room'
const ROLE_KEY = 'dautovtech_kolkhoz_room_role'

export type SyncRole = 'host' | 'follower' | null
/** idle = no room; live = connected; ended = host closed / code invalid */
export type RoomLiveStatus = 'idle' | 'live' | 'ended'

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
  const roomStatus = useState<RoomLiveStatus>('kolkhoz-room-status', () => 'idle')
  const endedMessage = useState<string>('kolkhoz-room-ended-msg', () => '')

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
    const savedRole = localStorage.getItem(ROLE_KEY) as SyncRole
    if (code && (savedRole === 'host' || savedRole === 'follower')) {
      roomCode.value = code
      role.value = savedRole
      roomStatus.value = 'live'
    }
  }

  const clearRoomMeta = () => {
    stopPolling()
    roomCode.value = null
    role.value = null
    revision.value = 0
    lastPushedAt.value = null
    syncError.value = ''
    persistMeta()
  }

  const clearRoom = () => {
    roomStatus.value = 'idle'
    endedMessage.value = ''
    clearRoomMeta()
  }

  /** Follower display-only: do not overwrite the host's local saved game. */
  const applyRemoteState = (remote: SessionGetResponse, { persistLocal = false } = {}) => {
    if (!remote.state || typeof remote.state !== 'object') return
    if ((remote.state as { version?: number }).version !== 1 && Object.keys(remote.state).length === 0) {
      return
    }
    applyingRemote.value = true
    try {
      const normalized = normalizeState(remote.state as Partial<KolkhozState>)
      Object.assign(store, normalized)
      if (persistLocal && import.meta.client) {
        localStorage.setItem('dautovtech_kolkhoz_v1', JSON.stringify({ ...store.$state }))
      }
      revision.value = remote.revision
    } finally {
      void nextTick(() => {
        applyingRemote.value = false
      })
    }
  }

  const markEnded = (message: string) => {
    stopPolling()
    const code = roomCode.value
    roomStatus.value = 'ended'
    endedMessage.value =
      message || (code ? `Встреча по коду ${code} завершена.` : 'Встреча завершена.')
    roomCode.value = null
    role.value = null
    revision.value = 0
    lastPushedAt.value = null
    syncError.value = ''
    persistMeta()
    // Clear board memory without wiping a host save on disk.
    Object.assign(store, createEmptyState())
  }

  const createRoom = async () => {
    syncError.value = ''
    endedMessage.value = ''
    const ok = await ensureAuthenticated()
    if (!ok) {
      syncError.value = 'Нужна авторизация на хабе, чтобы создать комнату.'
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
      roomStatus.value = 'live'
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
    endedMessage.value = ''
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
      roomStatus.value = 'live'
      persistMeta()
      applyRemoteState(remote, { persistLocal: false })
      startPolling()
      return true
    } catch {
      syncError.value = 'Комната не найдена или встреча уже завершена'
      roomStatus.value = 'idle'
      return false
    }
  }

  /** Host ends the meeting for everyone (code stops working). */
  const closeRoom = async () => {
    syncError.value = ''
    if (role.value !== 'host' || !roomCode.value) {
      clearRoom()
      return true
    }
    const code = roomCode.value
    try {
      await $fetch(apiUrl(`/api/v1/kolkhoz/sessions/${encodeURIComponent(code)}`), {
        method: 'DELETE',
        credentials: 'include',
        headers: authHeaders()
      })
    } catch {
      // Still clear local — room may already be gone.
    }
    clearRoomMeta()
    roomStatus.value = 'idle'
    endedMessage.value = `Встреча ${code} завершена. Создайте новую комнату, если нужна ещё одна трансляция.`
    // Restore host local game (follower mirror must not stay on the board).
    if (import.meta.client) store.hydrate()
    return true
  }

  /** TV / spectator disconnects without closing the host room. */
  const leaveRoom = () => {
    const wasFollower = role.value === 'follower'
    clearRoom()
    if (wasFollower && import.meta.client) {
      Object.assign(store, createEmptyState())
    }
  }

  /**
   * After reload: only resume follower if the room still exists on the server.
   * Avoids showing a dead “old sync” forever.
   */
  const resumeFollowerIfPossible = async () => {
    hydrateMeta()
    if (role.value !== 'follower' || !roomCode.value) return false
    const code = roomCode.value
    const ok = await joinRoom(code)
    if (!ok) {
      markEnded(`Комната ${code} больше недоступна. Введите новый код.`)
      return false
    }
    return true
  }

  const pushNow = async () => {
    if (role.value !== 'host' || !roomCode.value || roomStatus.value !== 'live') return
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
    } catch (error: unknown) {
      const status = (error as { statusCode?: number; status?: number })?.statusCode
        || (error as { status?: number })?.status
      if (status === 404) {
        markEnded('Комната закрыта на сервере. Создайте новую.')
        if (import.meta.client) store.hydrate()
        return
      }
      syncError.value = error instanceof Error ? error.message : 'Не удалось отправить обновление'
    }
  }

  const schedulePush = () => {
    if (role.value !== 'host' || !roomCode.value || roomStatus.value !== 'live') return
    if (applyingRemote.value) return
    if (pushTimer) clearTimeout(pushTimer)
    pushTimer = setTimeout(() => {
      void pushNow()
    }, 350)
  }

  const pollOnce = async () => {
    if (role.value !== 'follower' || !roomCode.value || roomStatus.value !== 'live') return
    try {
      const remote = await $fetch<SessionGetResponse>(
        apiUrl(`/api/v1/kolkhoz/sessions/${encodeURIComponent(roomCode.value)}`)
      )
      if (remote.revision !== revision.value) {
        applyRemoteState(remote, { persistLocal: false })
      }
      syncError.value = ''
    } catch {
      markEnded('Ведущий завершил встречу или комната недоступна. Введите новый код.')
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

  const isLive = computed(() => roomStatus.value === 'live' && Boolean(roomCode.value))

  return {
    roomCode,
    role,
    revision,
    syncError,
    lastPushedAt,
    roomStatus,
    endedMessage,
    isLive,
    username,
    tvUrl,
    hydrateMeta,
    createRoom,
    joinRoom,
    clearRoom,
    closeRoom,
    leaveRoom,
    resumeFollowerIfPossible,
    pushNow,
    schedulePush,
    startPolling,
    stopPolling,
    onLocalChange,
    pollOnce
  }
}
