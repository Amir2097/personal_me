import type { ProgressLog } from '~/types/academy'

const STORAGE_KEY = 'billiards_academy_progress_v1'

type AcademyState = {
  logs: Record<string, ProgressLog>
  syncStatus: 'idle' | 'syncing' | 'synced' | 'offline' | 'error'
  syncError: string
}

type ServerProgressItem = {
  exercise_id: string
  made: number
  attempts: number
  updated_at: string
}

const toMs = (iso: string) => {
  const value = Date.parse(iso)
  return Number.isFinite(value) ? value : 0
}

const mergeLogs = (
  local: Record<string, ProgressLog>,
  remote: ProgressLog[]
): Record<string, ProgressLog> => {
  const next = { ...local }
  for (const item of remote) {
    const existing = next[item.exerciseId]
    if (!existing || toMs(item.updatedAt) >= toMs(existing.updatedAt)) {
      next[item.exerciseId] = item
    }
  }
  return next
}

export const useAcademyStore = defineStore('academy', {
  state: (): AcademyState => ({
    logs: {},
    syncStatus: 'idle',
    syncError: ''
  }),
  getters: {
    byExercise: (state) => (exerciseId: string): ProgressLog | null => state.logs[exerciseId] || null
  },
  actions: {
    hydrate() {
      if (!import.meta.client) return
      try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (!raw) return
        const parsed = JSON.parse(raw) as AcademyState
        this.logs = parsed.logs || {}
      } catch {
        this.logs = {}
      }
    },
    persist() {
      if (!import.meta.client) return
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ logs: this.logs }))
    },
    recordResult(exerciseId: string, made: number, attempts: number) {
      this.logs[exerciseId] = {
        exerciseId,
        made: Math.max(0, Math.round(made)),
        attempts: Math.max(1, Math.round(attempts)),
        updatedAt: new Date().toISOString()
      }
      this.persist()
    },
    applyServerItems(items: ServerProgressItem[]) {
      const remote: ProgressLog[] = items.map((item) => ({
        exerciseId: item.exercise_id,
        made: item.made,
        attempts: item.attempts,
        updatedAt: item.updated_at
      }))
      this.logs = mergeLogs(this.logs, remote)
      this.persist()
    },
    exportItems(): ServerProgressItem[] {
      return Object.values(this.logs).map((log) => ({
        exercise_id: log.exerciseId,
        made: log.made,
        attempts: log.attempts,
        updated_at: log.updatedAt
      }))
    }
  }
})
