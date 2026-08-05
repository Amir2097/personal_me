import { defineStore } from 'pinia'
import {
  createEmptyState,
  normalizeState,
  type BankState,
  type BuyInKind,
  type CasualPenaltyConfig,
  type GameMode,
  type KolkhozState,
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
import {
  calcPartySettlement,
  createCasualParty,
  effectivePartyScore,
  hasOpenPartyActivity,
  partyPointsTotal,
  partyTargetNorm,
  potCasualBall,
  settleCasualParty
} from '~/utils/casual'
import { computeDebtTransfers } from '~/utils/debts'
import { applyCasualFoul } from '~/utils/casualPenalties'
import { applyDropout, previousPlayerId, processScore, undoEvent } from '~/utils/scoring'
import { claimTablePot, passTablePotMiss, placeTableFine, potForTable, returnTablePot } from '~/utils/pot'
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
      ),
    potByTableId: (state) => (tableId: string) => potForTable(state.tournament.pots, tableId),
    casualParty: (state) => state.casual.party,
    casualPartyTotal: (state) => (state.casual.party ? partyPointsTotal(state.casual.party) : 0),
    casualRackTotal: (state) => state.casual.party?.rackPointsTotal ?? 0,
    casualSessionEnded: (state) => Boolean(state.casual.sessionEndedAt),
    casualDebtTransfers: (state) => computeDebtTransfers(state.players),
    casualPartyNorm: (state) => {
      const party = state.casual.party
      if (!party) return 0
      const count = state.players.filter((player) => player.status === 'active').length
      return partyTargetNorm(count)
    },
    casualProjected: (state) => (playerId: string) => {
      const party = state.casual.party
      if (!party || partyPointsTotal(party) <= 0) return 0
      const ids = state.players.filter((player) => player.status === 'active').map((player) => player.id)
      const line = calcPartySettlement(party, state.players, ids, state.casual.ballPrice).find(
        (item) => item.playerId === playerId
      )
      return line?.deltaMoney ?? 0
    },
    casualEffectiveScore: (state) => (playerId: string) => {
      const party = state.casual.party
      const player = state.players.find((item) => item.id === playerId)
      if (!party || !player) return 0
      return effectivePartyScore(party, player)
    }
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
      stakePrice?: number
      startingStack?: number
      /** Tournament: record initial entry buy-in (money). Chips come from startingStack / entry chips. */
      entryMoney?: number
      entryChips?: number
    }) {
      const name = input.name.trim()
      if (!name) return
      if (this.players.length >= 48) return
      const chips =
        this.mode === 'casual'
          ? 0
          : input.entryChips ??
            input.startingStack ??
            this.tournament.bank.rebuyPreset.chips
      const player: Player = {
        id: uid(),
        name,
        category: input.category ?? 2,
        handicap: this.mode === 'casual' ? Math.max(0, Math.round(input.handicap ?? 0)) : input.handicap ?? 1,
        stakePrice:
          this.mode === 'casual' && input.stakePrice != null
            ? Math.max(1, Math.round(input.stakePrice))
            : undefined,
        startingStack: chips,
        balance: this.mode === 'casual' ? 0 : chips,
        status: 'active'
      }
      this.players.push(player)

      // Entry buy-in for both detailed and organizer tournament kinds.
      const money = input.entryMoney ?? this.tournament.bank.rebuyPreset.money
      if (this.mode === 'tournament' && money > 0) {
        this.tournament.buyIns.push({
          id: uid(),
          at: new Date().toISOString(),
          playerId: player.id,
          kind: 'rebuy',
          money,
          chips,
          note: 'Стартовый докуп',
          roundNumber: this.currentRound?.number
        })
      }
      this.persist()
    },
    updatePlayer(id: string, patch: Partial<Pick<Player, 'name' | 'category' | 'handicap' | 'startingStack' | 'balance' | 'stakePrice'>>) {
      const player = this.players.find((item) => item.id === id)
      if (!player) return
      if (patch.name !== undefined) player.name = patch.name.trim() || player.name
      if (patch.category !== undefined) player.category = patch.category
      if (patch.handicap !== undefined) {
        player.handicap =
          this.mode === 'casual' ? Math.max(0, Math.round(patch.handicap)) : patch.handicap
      }
      if (patch.balance !== undefined) player.balance = patch.balance
      if (patch.stakePrice !== undefined) {
        player.stakePrice = Math.max(1, Math.round(patch.stakePrice))
      }
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
      // Return open pot contributions if the only contributor left; otherwise drop their share from pots.
      this.tournament.pots = this.tournament.pots
        .map((pot) => {
          const kept = pot.contributions.filter((part) => part.playerId !== id)
          if (!kept.length) return null
          return {
            ...pot,
            contributions: kept,
            amount: kept.reduce((sum, part) => sum + part.amount, 0),
            circlePlayerIds: pot.circlePlayerIds.filter((playerId) => playerId !== id)
          }
        })
        .filter((pot): pot is NonNullable<typeof pot> => Boolean(pot))
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
    setCasualPenalties(patch: Partial<CasualPenaltyConfig>) {
      if (patch.mode !== undefined) this.casual.penalties.mode = patch.mode
      if (patch.usePersonalStake !== undefined) {
        this.casual.penalties.usePersonalStake = patch.usePersonalStake
      }
      this.persist()
    },
    setCasualBallPrice(value: number) {
      this.casual.ballPrice = Math.max(1, Math.round(value))
      this.persist()
    },
    /** @deprecated Use setCasualBallPrice */
    setCasualBaseUnit(value: number) {
      this.setCasualBallPrice(value)
    },
    updateBall(id: string, patch: Partial<SpecialBall>) {
      const ball = this.casual.balls.find((item) => item.id === id)
      if (!ball) return
      if (patch.label !== undefined) ball.label = patch.label
      if (patch.color !== undefined) ball.color = patch.color
      if (patch.price !== undefined) ball.price = Math.round(patch.price)
      if (patch.partyRole !== undefined) ball.partyRole = patch.partyRole === 'extra' ? 'extra' : 'rack'
      this.persist()
    },
    addBall(ball?: Partial<SpecialBall>) {
      this.casual.balls.push({
        id: uid(),
        label: ball?.label || 'Шар',
        price: ball?.price ?? this.casual.ballPrice,
        color: ball?.color || '#94a3b8',
        partyRole: ball?.partyRole === 'extra' ? 'extra' : 'rack'
      })
      this.persist()
    },
    removeBall(ballId: string) {
      const ball = this.casual.balls.find((b) => b.id === ballId)
      if (!ball) return
      // Разрешаем удалять только пользовательские шары.
      if (['standard', 'yellow', 'red', 'black'].includes(ballId)) return
      // Настройки предполагаются до игры; если в партию уже есть активность — блокируем.
      if (this.casual.party && hasOpenPartyActivity(this.casual.party)) return
      this.casual.balls = this.casual.balls.filter((b) => b.id !== ballId)
      this.persist()
    },
    ensureCasualParty() {
      if (!this.casual.party) {
        this.casual.party = createCasualParty(1)
        this.persist()
      }
    },
    potCasualBall(scorerId: string, ballId: string, tablePlayerIds: string[]) {
      if (this.mode !== 'casual') throw new Error('Only for casual mode')
      if (this.casual.sessionEndedAt) throw new Error('Встреча уже завершена.')
      const ball = this.casual.balls.find((item) => item.id === ballId)
      if (!ball) throw new Error(`Unknown ball: ${ballId}`)
      this.ensureCasualParty()
      const party = this.casual.party!
      const prevId = previousPlayerId(tablePlayerIds, scorerId)
      const prev = prevId ? this.players.find((player) => player.id === prevId) : null
      if (!prev) throw new Error('Need at least 2 active players.')

      const result = potCasualBall(
        party,
        ball,
        this.casual.ballPrice,
        tablePlayerIds,
        scorerId,
        this.casualTableId,
        prev.name
      )
      this.casual.party = result.party
      this.events.push(result.event)
      this.persist()
      return result
    },
    applyCasualFoul(offenderId: string, tablePlayerIds: string[]) {
      if (this.mode !== 'casual') throw new Error('Only for casual mode')
      if (this.casual.sessionEndedAt) throw new Error('Встреча уже завершена.')
      this.ensureCasualParty()
      const result = applyCasualFoul(
        this.casual.party!,
        this.players,
        tablePlayerIds,
        offenderId,
        this.casual.penalties,
        this.casual.ballPrice,
        this.casualTableId
      )
      this.casual.party = result.party
      this.players = result.players
      this.events.push(result.event)
      this.persist()
      return result
    },
    settleCasualParty(tablePlayerIds: string[]) {
      if (this.mode !== 'casual') throw new Error('Only for casual mode')
      if (this.casual.sessionEndedAt) throw new Error('Встреча уже завершена.')
      if (!this.casual.party) throw new Error('Партия ещё не начата.')
      const result = settleCasualParty(
        this.casual.party,
        this.players,
        tablePlayerIds,
        this.casual.ballPrice,
        this.casualTableId
      )
      this.players = result.players
      this.casual.party = result.party
      this.events.push(result.event)
      this.persist()
      return result
    },
    endCasualSession(tablePlayerIds: string[]) {
      if (this.mode !== 'casual') throw new Error('Only for casual mode')
      if (this.casual.sessionEndedAt) return

      if (this.casual.party && hasOpenPartyActivity(this.casual.party)) {
        this.settleCasualParty(tablePlayerIds)
      }

      const balances = Object.fromEntries(this.players.map((player) => [player.id, player.balance]))
      const endedAt = new Date().toISOString()
      this.casual.sessionEndedAt = endedAt
      this.casual.party = null
      this.events.push({
        id: uid(),
        at: endedAt,
        mode: 'casual',
        tableId: this.casualTableId,
        scorerId: this.players[0]?.id || 'session',
        ballId: 'session-end',
        deltas: {},
        kind: 'session_end',
        note: 'Встреча завершена — итоговый расчёт.',
        sessionBalances: balances
      })
      this.persist()
    },
    resetCasualMeeting() {
      if (this.mode !== 'casual') return
      this.players = this.players.map((player) => ({ ...player, balance: 0 }))
      this.events = []
      this.casual.party = null
      this.casual.sessionEndedAt = null
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
      // Detailed: open pots return before reseat (previous round circle is over).
      if (this.isDetailedTournament) {
        for (const pot of [...this.tournament.pots]) {
          const result = returnTablePot(this.players, this.tournament.pots, pot.tableId)
          this.players = result.players
          this.tournament.pots = result.pots
          if (result.event) this.events.push(result.event)
        }
      }
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
      if (this.mode === 'casual') {
        this.potCasualBall(scorerId, ballId, tablePlayerIds)
        return
      }
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

      // Next scorer also takes open fine pot (общак) on this table.
      const claim = claimTablePot(this.players, this.tournament.pots, tableId, scorerId)
      this.players = claim.players
      this.tournament.pots = claim.pots
      if (claim.event) {
        this.events.push(claim.event)
        result.event.note = `${result.event.note || ''} + общак ${claim.claimed}`.trim()
      }
      this.persist()
    },
    /**
     * Player puts chips into table pot (штраф → общак). Detailed tournament only.
     * Default amount = round tariff of group 1 (max stake), regardless of offender's group.
     */
    placeFine(tableId: string, playerId: string, tablePlayerIds: string[], amount?: number) {
      if (!this.isDetailedTournament) {
        throw new Error('Fines are only available in detailed tournament mode.')
      }
      const player = this.players.find((item) => item.id === playerId)
      if (!player) return
      const tariff = this.currentRound?.tariffs[1] ?? 0
      const chips = amount ?? tariff
      const result = placeTableFine(
        this.players,
        this.tournament.pots,
        tableId,
        tablePlayerIds,
        playerId,
        chips
      )
      this.players = result.players
      this.tournament.pots = result.pots
      this.events.push(result.event)
      this.persist()
    },
    /** Group-1 tariff for the current round (default fine / max stake). */
    fineDefaultAmount() {
      return this.currentRound?.tariffs[1] ?? 0
    },
    /** Claim open pot without ball scoring (detailed helper / rare manual path). */
    claimPot(tableId: string, scorerId: string) {
      if (!this.isDetailedTournament) {
        throw new Error('Pot claim is only available in detailed tournament mode.')
      }
      const result = claimTablePot(this.players, this.tournament.pots, tableId, scorerId)
      if (!result.event) return
      this.players = result.players
      this.tournament.pots = result.pots
      this.events.push(result.event)
      this.persist()
    },
    /** Circle ended with no score — return pot to contributors. Detailed only. */
    returnPot(tableId: string) {
      if (!this.isDetailedTournament) return
      const result = returnTablePot(this.players, this.tournament.pots, tableId)
      if (!result.event) return
      this.players = result.players
      this.tournament.pots = result.pots
      this.events.push(result.event)
      this.persist()
    },
    /** Mark «мимо» for pass cursor; auto-returns pot when the circle completes. */
    passPotMiss(tableId: string, playerId: string) {
      if (!this.isDetailedTournament) return false
      const result = passTablePotMiss(this.players, this.tournament.pots, tableId, playerId)
      this.players = result.players
      this.tournament.pots = result.pots
      if (result.event) this.events.push(result.event)
      this.persist()
      return Boolean(result.event)
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

      if (event.kind === 'fine_place') {
        this.players = undoEvent(this.players, event)
        const pot = potForTable(this.tournament.pots, event.tableId)
        if (pot) {
          const amount = event.potAmount || 0
          const nextContrib = [...pot.contributions]
          const last = nextContrib[nextContrib.length - 1]
          if (last && last.playerId === event.scorerId && last.amount === amount) {
            nextContrib.pop()
          } else {
            const idx = nextContrib.findIndex(
              (part) => part.playerId === event.scorerId && part.amount === amount
            )
            if (idx >= 0) nextContrib.splice(idx, 1)
          }
          if (!nextContrib.length) {
            this.tournament.pots = this.tournament.pots.filter((item) => item.tableId !== event.tableId)
          } else {
            this.tournament.pots = this.tournament.pots.map((item) =>
              item.tableId === event.tableId
                ? {
                    ...item,
                    contributions: nextContrib,
                    amount: nextContrib.reduce((sum, part) => sum + part.amount, 0)
                  }
                : item
            )
          }
        }
      } else if (event.kind === 'fine_claim' || event.kind === 'fine_return') {
        this.players = undoEvent(this.players, event)
        if (event.potSnapshot) {
          this.tournament.pots = [
            ...this.tournament.pots.filter((item) => item.tableId !== event.tableId),
            event.potSnapshot
          ]
        }
      } else if (event.kind === 'party_settle') {
        this.players = undoEvent(this.players, event)
        if (event.partySnapshot) {
          const orderMap = new Map(event.partySnapshot.playerOrder.map((id, index) => [id, index]))
          this.players = [...this.players].sort(
            (a, b) => (orderMap.get(a.id) ?? 999) - (orderMap.get(b.id) ?? 999)
          )
          this.casual.party = {
            ...event.partySnapshot.party,
            pointsByPlayer: { ...event.partySnapshot.party.pointsByPlayer }
          }
        }
      } else if (
        event.mode === 'casual' &&
        event.kind === 'score' &&
        event.partyPointsDelta != null &&
        this.casual.party
      ) {
        const delta = event.partyPointsDelta
        if (event.partyPointRole === 'extra') {
          const nextExtra = { ...this.casual.party.extraPointsByPlayer }
          nextExtra[event.scorerId] = (nextExtra[event.scorerId] || 0) - delta
          if ((nextExtra[event.scorerId] || 0) <= 0) delete nextExtra[event.scorerId]
          this.casual.party = { ...this.casual.party, extraPointsByPlayer: nextExtra }
        } else {
          const nextRack = { ...this.casual.party.rackPointsByPlayer }
          nextRack[event.scorerId] = (nextRack[event.scorerId] || 0) - delta
          if ((nextRack[event.scorerId] || 0) <= 0) delete nextRack[event.scorerId]
          this.casual.party = {
            ...this.casual.party,
            ballIndex: Math.max(0, (event.partyBallIndex ?? this.casual.party.ballIndex) - 1),
            rackPointsTotal: Math.max(0, this.casual.party.rackPointsTotal - delta),
            rackPointsByPlayer: nextRack
          }
        }
      } else if (event.kind === 'casual_foul') {
        if (event.foulSnapshot?.playerBalances) {
          this.players = this.players.map((player) => ({
            ...player,
            balance: event.foulSnapshot!.playerBalances![player.id] ?? player.balance
          }))
        }
        if (event.foulSnapshot?.party) {
          this.casual.party = {
            ...event.foulSnapshot.party,
            rackPointsByPlayer: { ...event.foulSnapshot.party.rackPointsByPlayer },
            extraPointsByPlayer: { ...event.foulSnapshot.party.extraPointsByPlayer },
            ballDebtByPlayer: { ...event.foulSnapshot.party.ballDebtByPlayer }
          }
        }
      } else if (event.kind === 'session_end') {
        this.casual.sessionEndedAt = null
      } else {
        this.players = undoEvent(this.players, event)
      }
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
