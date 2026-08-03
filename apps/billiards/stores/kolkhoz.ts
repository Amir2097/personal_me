import { defineStore } from 'pinia'
import {
  createEmptyState,
  type GameMode,
  type KolkhozState,
  type Player,
  type PlayerCategory,
  type SpecialBall
} from '~/types/kolkhoz'
import { applyDropout, processScore, undoEvent } from '~/utils/scoring'
import { movePlayerToTable, seatPlayers } from '~/utils/seating'

const STORAGE_KEY = 'dautovtech_kolkhoz_v1'

const loadState = (): KolkhozState => {
  if (typeof window === 'undefined') return createEmptyState()
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return createEmptyState()
    const parsed = JSON.parse(raw) as KolkhozState
    if (parsed.version !== 1) return createEmptyState()
    return parsed
  } catch {
    return createEmptyState()
  }
}

const uid = () =>
  typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `p_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`

export const useKolkhozStore = defineStore('kolkhoz', {
  state: (): KolkhozState => createEmptyState(),
  getters: {
    activePlayers: (state) => state.players.filter((player) => player.status === 'active'),
    eliminatedPlayers: (state) => state.players.filter((player) => player.status === 'eliminated'),
    leaderboard: (state) =>
      [...state.players].sort((a, b) => b.balance - a.balance || a.name.localeCompare(b.name)),
    currentRound: (state) => state.tournament.rounds[state.tournament.currentRoundIndex] ?? null,
    casualTableId: () => 'casual-main'
  },
  actions: {
    hydrate() {
      Object.assign(this, loadState())
    },
    persist() {
      if (typeof window === 'undefined') return
      this.updatedAt = new Date().toISOString()
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...this.$state }))
    },
    resetAll() {
      Object.assign(this, createEmptyState())
      this.persist()
    },
    setMode(mode: GameMode) {
      this.mode = mode
      this.persist()
    },
    addPlayer(input: {
      name: string
      category?: PlayerCategory
      handicap?: number
      startingStack?: number
    }) {
      const name = input.name.trim()
      if (!name) return
      if (this.players.length >= 24) return
      const startingStack = input.startingStack ?? 100
      const player: Player = {
        id: uid(),
        name,
        category: input.category ?? 2,
        handicap: input.handicap ?? 1,
        startingStack,
        balance: startingStack,
        status: 'active'
      }
      this.players.push(player)
      this.persist()
    },
    updatePlayer(id: string, patch: Partial<Pick<Player, 'name' | 'category' | 'handicap' | 'startingStack'>>) {
      const player = this.players.find((item) => item.id === id)
      if (!player) return
      if (patch.name !== undefined) player.name = patch.name.trim() || player.name
      if (patch.category !== undefined) player.category = patch.category
      if (patch.handicap !== undefined) player.handicap = patch.handicap
      if (patch.startingStack !== undefined) {
        const diff = patch.startingStack - player.startingStack
        player.startingStack = patch.startingStack
        player.balance += diff
      }
      this.persist()
    },
    removePlayer(id: string) {
      this.players = this.players.filter((player) => player.id !== id)
      this.tournament.tables = this.tournament.tables.map((table) => ({
        ...table,
        playerIds: table.playerIds.filter((playerId) => playerId !== id)
      }))
      this.persist()
    },
    setCasualBaseUnit(value: number) {
      this.casual.baseUnit = Math.max(0.1, value)
      this.persist()
    },
    updateBall(id: string, patch: Partial<SpecialBall>) {
      const ball = this.casual.balls.find((item) => item.id === id)
      if (!ball) return
      Object.assign(ball, patch)
      this.persist()
    },
    addBall(ball?: Partial<SpecialBall>) {
      this.casual.balls.push({
        id: uid(),
        label: ball?.label || 'Шар',
        multiplier: ball?.multiplier ?? 1,
        color: ball?.color || '#94a3b8'
      })
      this.persist()
    },
    setTableCount(count: number) {
      this.tournament.tableCount = Math.max(1, Math.min(12, count))
      this.persist()
    },
    reseat() {
      this.tournament.tables = seatPlayers(this.players, this.tournament.tableCount)
      this.persist()
    },
    movePlayer(playerId: string, tableId: string) {
      this.tournament.tables = movePlayerToTable(this.tournament.tables, playerId, tableId)
      this.persist()
    },
    updateRound(
      index: number,
      patch: Partial<{ durationMinutes: number; tariffs: Record<PlayerCategory, number> }>
    ) {
      const round = this.tournament.rounds[index]
      if (!round) return
      if (patch.durationMinutes !== undefined) round.durationMinutes = patch.durationMinutes
      if (patch.tariffs) round.tariffs = { ...round.tariffs, ...patch.tariffs }
      this.persist()
    },
    addRound() {
      const n = this.tournament.rounds.length + 1
      this.tournament.rounds.push({
        number: n,
        durationMinutes: 20,
        tariffs: { 1: 4 + n, 2: 3 + n, 3: 2 + n }
      })
      this.persist()
    },
    setCurrentRound(index: number) {
      if (index < 0 || index >= this.tournament.rounds.length) return
      this.tournament.currentRoundIndex = index
      this.persist()
    },
    /** Move to another round, reshuffle active players across tables, reset timer. */
    advanceRound(index: number) {
      if (index < 0 || index >= this.tournament.rounds.length) return
      if (this.tournament.currentRoundIndex === index) return
      this.tournament.currentRoundIndex = index
      this.tournament.roundEndsAt = null
      this.tournament.tables = seatPlayers(this.players, this.tournament.tableCount)
      this.persist()
    },
    startRoundTimer() {
      const round = this.currentRound
      if (!round) return
      this.tournament.roundEndsAt = new Date(Date.now() + round.durationMinutes * 60_000).toISOString()
      this.persist()
    },
    clearRoundTimer() {
      this.tournament.roundEndsAt = null
      this.persist()
    },
    setTimerMuted(muted: boolean) {
      this.tournament.timerMuted = muted
      this.persist()
    },
    score(tableId: string, scorerId: string, ballId: string, tablePlayerIds: string[]) {
      if (!this.mode) throw new Error('Mode is not selected')
      const result = processScore({
        mode: this.mode,
        players: this.players,
        tableId,
        scorerId,
        ballId,
        tablePlayerIds,
        round: this.currentRound ?? undefined,
        casual: this.casual
      })
      this.players = result.players
      this.events.push(result.event)
      this.persist()
    },
    dropout(tableId: string, playerId: string) {
      const result = applyDropout(this.players, playerId, tableId)
      this.players = result.players
      this.events.push(result.event)
      this.persist()
    },
    undoLast() {
      const event = this.events.pop()
      if (!event) return
      this.players = undoEvent(this.players, event)
      this.persist()
    },
    exportJson() {
      return JSON.stringify(this.$state, null, 2)
    },
    importJson(raw: string) {
      const parsed = JSON.parse(raw) as KolkhozState
      if (parsed.version !== 1) throw new Error('Unsupported save version')
      Object.assign(this, parsed)
      this.persist()
    }
  }
})
