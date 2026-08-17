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

type SessionCreateResponse = {
  code: string
  revision: number
}

/**
 * Host pushes cup Pinia state; TV polls by room code.
 */
export const useCupSync = () => {
  const { apiUrl, authHeaders, username, ensureAuthenticated } = useHubAuth()
  const { canSyncRoom, syncDeniedMessage } = useGameAccess()
  const { appHref } = useAppBase()
  const store = useCupStore()

  const roomCode = useState<string | null>('cup-room-code', () => null)
  const role = useState<CupSyncRole>('cup-room-role', () => null)
  const revision = useState<number>('cup-room-revision', () => 0)
  const syncError = useState<string>('cup-sync-error', () => '')
  const lastPushedAt = useState<string | null>('cup-last-pushed', () => null)
  const roomStatus = useState<CupRoomLiveStatus>('cup-room-status', () => 'idle')
  const endedMessage = useState<string>('cup-room-ended-msg', () => '')
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

  const markEnded = (message: string) => {
    stopPolling()
    const code = roomCode.value
    roomStatus.value = 'ended'
    endedMessage.value =
      message || (code ? `Трансляция по коду ${code} завершена.` : 'Трансляция завершена.')
    roomCode.value = null
    role.value = null
    revision.value = 0
    lastPushedAt.value = null
    syncError.value = ''
    persistMeta()
  }

  const pushNow = async () => {
    if (role.value !== 'host' || !roomCode.value || roomStatus.value !== 'live') return
    if (applyingRemote.value) return
    try {
      const remote = await $fetch<SessionGetResponse>(
        apiUrl(`/api/v1/cup/sessions/${encodeURIComponent(roomCode.value)}`)
      )
      if (remote.revision > revision.value) {
        applyRemoteState(remote)
        return
      }
      const result = await $fetch<{ revision: number; updated_at: string }>(
        apiUrl(`/api/v1/cup/sessions/${encodeURIComponent(roomCode.value)}`),
        {
          method: 'PUT',
          credentials: 'include',
          headers: authHeaders(),
          body: {
            state: store.exportSnapshot(),
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
        return
      }
      syncError.value = error instanceof Error ? error.message : 'Не удалось отправить обновление'
    }
  }

  const createRoom = async () => {
    syncError.value = ''
    endedMessage.value = ''
    if (!canSyncRoom.value) {
      syncError.value = syncDeniedMessage
      return null
    }
    const ok = await ensureAuthenticated()
    if (!ok) {
      syncError.value = 'Нужен вход оператора и связь с API Цифрового Сукна.'
      return null
    }
    try {
      const created = await $fetch<SessionCreateResponse>(apiUrl('/api/v1/cup/sessions'), {
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
      startPolling()
      return created.code
    } catch (error) {
      const status = (error as { statusCode?: number })?.statusCode
      syncError.value =
        status === 403
          ? syncDeniedMessage
          : error instanceof Error
            ? error.message
            : 'Не удалось создать комнату'
      return null
    }
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

  const pollOnce = async () => {
    if (!roomCode.value || roomStatus.value !== 'live') return
    if (role.value !== 'follower' && role.value !== 'host') return
    try {
      const remote = await $fetch<SessionGetResponse>(
        apiUrl(`/api/v1/cup/sessions/${encodeURIComponent(roomCode.value)}`)
      )
      if (remote.revision !== revision.value) {
        applyRemoteState(remote)
      }
      syncError.value = ''
    } catch {
      if (role.value === 'host') return
      markEnded('Ведущий завершил трансляцию или комната недоступна. Введите новый код.')
    }
  }

  const startPolling = (intervalMs = 1000) => {
    stopPolling()
    if (!import.meta.client) return
    pollTimer = setInterval(() => {
      void pollOnce()
    }, intervalMs)
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
        apiUrl(`/api/v1/cup/sessions/${encodeURIComponent(normalized)}`)
      )
      roomCode.value = remote.code
      role.value = 'follower'
      revision.value = remote.revision
      roomStatus.value = 'live'
      persistMeta()
      applyRemoteState(remote)
      startPolling()
      return true
    } catch {
      syncError.value = 'Комната не найдена или трансляция уже завершена'
      roomStatus.value = 'idle'
      return false
    }
  }

  const resumeFollowerIfPossible = async () => {
    hydrateMeta()
    if (role.value === 'host' && roomCode.value) {
      startPolling()
      return true
    }
    if (role.value !== 'follower' || !roomCode.value) return false
    const code = roomCode.value
    const ok = await joinRoom(code)
    if (!ok) {
      markEnded(`Комната ${code} больше недоступна. Введите новый код.`)
      return false
    }
    return true
  }

  const closeRoom = async () => {
    syncError.value = ''
    if (role.value !== 'host' || !roomCode.value) {
      clearRoom()
      return true
    }
    const code = roomCode.value
    try {
      await $fetch(apiUrl(`/api/v1/cup/sessions/${encodeURIComponent(code)}`), {
        method: 'DELETE',
        credentials: 'include',
        headers: authHeaders()
      })
    } catch {
      /* room may already be gone */
    }
    clearRoomMeta()
    roomStatus.value = 'idle'
    endedMessage.value = `Трансляция ${code} завершена.`
    if (import.meta.client) store.hydrate()
    return true
  }

  const leaveRoom = () => {
    clearRoom()
  }

  const applyServerSession = (remote: SessionGetResponse) => {
    applyRemoteState(remote)
  }

  const claimPlayer = async (playerId: string) => {
    if (!roomCode.value) return false
    const remote = await $fetch<SessionGetResponse>(
      apiUrl(`/api/v1/cup/sessions/${encodeURIComponent(roomCode.value)}/claim`),
      {
        method: 'POST',
        credentials: 'include',
        headers: authHeaders(),
        body: { player_id: playerId }
      }
    )
    applyRemoteState(remote)
    return true
  }

  const postMatchEvent = async (payload: {
    match_id: string
    action: 'add_ball' | 'undo_ball' | 'award_frame' | 'complete'
    side?: 'A' | 'B'
    winner_id?: string
  }) => {
    if (!roomCode.value) return false
    const remote = await $fetch<SessionGetResponse>(
      apiUrl(`/api/v1/cup/sessions/${encodeURIComponent(roomCode.value)}/events`),
      {
        method: 'POST',
        credentials: 'include',
        headers: authHeaders(),
        body: payload
      }
    )
    applyRemoteState(remote)
    return true
  }

  const tvUrl = computed(() => {
    if (!import.meta.client || !roomCode.value) return ''
    return appHref('cup/tv', { room: roomCode.value })
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
    schedulePush,
    onLocalChange,
    pushNow,
    closeRoom,
    leaveRoom,
    clearRoom,
    startPolling,
    stopPolling,
    resumeFollowerIfPossible,
    pollOnce,
    applyServerSession,
    claimPlayer,
    postMatchEvent
  }
}
