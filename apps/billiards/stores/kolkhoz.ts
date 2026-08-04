import { defineStore } from 'pinia'
import {
  createEmptyState,
  normalizeState,
  type BankState,
  type BuyInKind,
  type GameMode,
  type KolkhozState,
  type Player,
  type PlayerCategory,
  type SpecialBall,
  type TournamentKind
} from '~/types/kolkhoz'
import {
  calcHouseCut,
  calcPrizePool,
  playerBoughtChips,
  playerPaid,
  splitPrizes,
  sumMoney
} from '~/utils/bank'
import { applyDropout, processScore, undoEvent } from '~/utils/scoring'
import { movePlayerToTable, seatPlayers, ensureTableSlots } from '~/utils/seating'

const STORAGE_KEY = 'dautovtech_kolkhoz_v1'

const loadState = (): KolkhozState => {
  if (typeof window === 'undefined') return createEmptyState()
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return createEmptyState()
    const parsed = JSON.parse(raw) as Partial<KolkhozState>
    if (parsed.version !== 1) return createEmptyState()
    return normalizeState(parsed)
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
    casualTableId: () => 'casual-main',
    isOrganizer: (state) => state.mode === 'tournament' && state.tournament.kind === 'organizer',
    isDetailedTournament: (state) => state.mode === 'tournament' && state.tournament.kind === 'detailed',
    timerIsPaused: (state) => state.tournament.timerPausedRemainingMs != null,
    timerIsRunning: (state) => Boolean(state.tournament.roundEndsAt),
    totalBank: (state) => sumMoney(state.tournament.buyIns),
    prizePool: (state) => calcPrizePool(sumMoney(state.tournament.buyIns), state.tournament.bank.prizePercent),
    houseCut: (state) => calcHouseCut(sumMoney(state.tournament.buyIns), state.tournament.bank.prizePercent),
    prizeBreakdown: (state) =>
      splitPrizes(
        calcPrizePool(sumMoney(state.tournament.buyIns), state.tournament.bank.prizePercent),
        state.tournament.bank.prizePlaces
      )
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
    setTournamentKind(kind: TournamentKind) {
      this.mode = 'tournament'
      this.tournament.kind = kind
      this.persist()
    },
    addPlayer(input: {
      name: string
      category?: PlayerCategory
      handicap?: number
      startingStack?: number
      /** Organizer: record initial entry buy-in (money). Chips come from startingStack / entry chips. */
      entryMoney?: number
      entryChips?: number
    }) {
      const name = input.name.trim()
      if (!name) return
      if (this.players.length >= 48) return
      const chips =
        input.entryChips ??
        input.startingStack ??
        (this.tournament.kind === 'organizer' ? this.tournament.bank.entryPreset.chips : 20)
      const player: Player = {
        id: uid(),
        name,
        category: input.category ?? 2,
        handicap: input.handicap ?? 1,
        startingStack: chips,
        balance: chips,
        status: 'active'
      }
      this.players.push(player)

      const money =
        input.entryMoney ??
        (this.tournament.kind === 'organizer' ? this.tournament.bank.entryPreset.money : 0)
      if (this.tournament.kind === 'organizer' && money > 0) {
        this.tournament.buyIns.push({
          id: uid(),
          at: new Date().toISOString(),
          playerId: player.id,
          kind: 'entry',
          money,
          chips,
          note: 'Стартовый взнос',
          roundNumber: this.currentRound?.number
        })
      }
      this.persist()
    },
    updatePlayer(id: string, patch: Partial<Pick<Player, 'name' | 'category' | 'handicap' | 'startingStack' | 'balance'>>) {
      const player = this.players.find((item) => item.id === id)
      if (!player) return
      if (patch.name !== undefined) player.name = patch.name.trim() || player.name
      if (patch.category !== undefined) player.category = patch.category
      if (patch.handicap !== undefined) player.handicap = patch.handicap
      if (patch.balance !== undefined) player.balance = patch.balance
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
      this.tournament.buyIns = this.tournament.buyIns.filter((item) => item.playerId !== id)
      this.persist()
    },
    updateBank(patch: Partial<BankState>) {
      if (patch.prizePercent !== undefined) {
        this.tournament.bank.prizePercent = Math.max(0, Math.min(100, patch.prizePercent))
      }
      if (patch.currencyLabel !== undefined) this.tournament.bank.currencyLabel = patch.currencyLabel
      if (patch.entryPreset) this.tournament.bank.entryPreset = { ...this.tournament.bank.entryPreset, ...patch.entryPreset }
      if (patch.rebuyPreset) this.tournament.bank.rebuyPreset = { ...this.tournament.bank.rebuyPreset, ...patch.rebuyPreset }
      if (patch.addonPreset) this.tournament.bank.addonPreset = { ...this.tournament.bank.addonPreset, ...patch.addonPreset }
      if (patch.prizePlaces) this.tournament.bank.prizePlaces = patch.prizePlaces.map((p) => ({ ...p }))
      this.persist()
    },
    setPrizePlace(place: number, percent: number) {
      const list = this.tournament.bank.prizePlaces
      const row = list.find((item) => item.place === place)
      if (row) row.percent = Math.max(0, Math.min(100, percent))
      else list.push({ place, percent: Math.max(0, Math.min(100, percent)) })
      list.sort((a, b) => a.place - b.place)
      this.persist()
    },
    recordBuyIn(input: {
      playerId: string
      kind: BuyInKind
      money: number
      chips: number
      note?: string
      addChipsToBalance?: boolean
    }) {
      const player = this.players.find((item) => item.id === input.playerId)
      if (!player) return
      const money = Math.max(0, Number(input.money) || 0)
      const chips = Math.max(0, Number(input.chips) || 0)
      if (money <= 0 && chips <= 0) return

      this.tournament.buyIns.push({
        id: uid(),
        at: new Date().toISOString(),
        playerId: input.playerId,
        kind: input.kind,
        money,
        chips,
        note: input.note,
        roundNumber: this.currentRound?.number
      })

      if (input.addChipsToBalance !== false && chips > 0) {
        player.balance += chips
      }
      this.persist()
    },
    removeBuyIn(buyInId: string, reverseChips = true) {
      const index = this.tournament.buyIns.findIndex((item) => item.id === buyInId)
      if (index < 0) return
      const [removed] = this.tournament.buyIns.splice(index, 1)
      if (reverseChips && removed) {
        const player = this.players.find((item) => item.id === removed.playerId)
        if (player) player.balance = Math.max(0, player.balance - (removed.chips || 0))
      }
      this.persist()
    },
    playerPaidAmount(playerId: string) {
      return playerPaid(this.tournament.buyIns, playerId)
    },
    playerBoughtChipsAmount(playerId: string) {
      return playerBoughtChips(this.tournament.buyIns, playerId)
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
      this.tournament.tables = ensureTableSlots(this.tournament.tableCount, this.tournament.tables)
      this.persist()
    },
    /** Ensure table slots exist so hall numbers can be edited before seating. */
    ensureTables() {
      this.tournament.tables = ensureTableSlots(this.tournament.tableCount, this.tournament.tables)
      this.persist()
    },
    reseat() {
      this.tournament.tables = seatPlayers(this.players, this.tournament.tableCount, this.tournament.tables)
      this.persist()
    },
    setTableNumber(tableId: string, number: number) {
      const table = this.tournament.tables.find((item) => item.id === tableId)
      if (!table) return
      const next = Math.max(1, Math.min(99, Math.round(number) || 1))
      table.number = next
      table.label = `Стол №${next}`
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
      this.tournament.timerPausedRemainingMs = null
      this.tournament.tables = seatPlayers(this.players, this.tournament.tableCount, this.tournament.tables)
      this.persist()
    },
    startRoundTimer() {
      const round = this.currentRound
      if (!round) return
      this.tournament.timerPausedRemainingMs = null
      this.tournament.roundEndsAt = new Date(Date.now() + round.durationMinutes * 60_000).toISOString()
      this.persist()
    },
    pauseRoundTimer() {
      if (!this.tournament.roundEndsAt) return
      const left = Math.max(0, new Date(this.tournament.roundEndsAt).getTime() - Date.now())
      this.tournament.timerPausedRemainingMs = left
      this.tournament.roundEndsAt = null
      this.persist()
    },
    resumeRoundTimer() {
      const left = this.tournament.timerPausedRemainingMs
      if (left == null || left <= 0) {
        this.tournament.timerPausedRemainingMs = null
        this.persist()
        return
      }
      this.tournament.roundEndsAt = new Date(Date.now() + left).toISOString()
      this.tournament.timerPausedRemainingMs = null
      this.persist()
    },
    clearRoundTimer() {
      this.tournament.roundEndsAt = null
      this.tournament.timerPausedRemainingMs = null
      this.persist()
    },
    setTimerMuted(muted: boolean) {
      this.tournament.timerMuted = muted
      this.persist()
    },
    score(tableId: string, scorerId: string, ballId: string, tablePlayerIds: string[]) {
      if (!this.mode) throw new Error('Mode is not selected')
      if (this.isOrganizer) throw new Error('Scoring is disabled in organizer mode')
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
    reinstate(playerId: string) {
      const player = this.players.find((item) => item.id === playerId)
      if (!player) return
      player.status = 'active'
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
      const parsed = JSON.parse(raw) as Partial<KolkhozState>
      if (parsed.version !== 1) throw new Error('Unsupported save version')
      Object.assign(this, normalizeState(parsed))
      this.persist()
    }
  }
})
