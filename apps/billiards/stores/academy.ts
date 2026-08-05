import type { ProgressLog } from '~/types/academy'

const STORAGE_KEY = 'billiards_academy_progress_v1'

type AcademyState = {
  logs: Record<string, ProgressLog>
}

export const useAcademyStore = defineStore('academy', {
  state: (): AcademyState => ({
    logs: {}
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
    }
  }
})
