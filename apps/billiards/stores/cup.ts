import { defineStore } from 'pinia'
import {
  bundleToCupState,
  createEmptyCupBundle,
  createEmptyCupState,
  createEmptyCupWorkspace,
  cupStateToBundle,
  cupUid,
  normalizeCupState,
  normalizeCupWorkspace,
  type CupFormat,
  type CupPlayer,
  type CupState,
  type CupTournamentBundle,
  type CupWorkspace,
  type ShotClockState
} from '~/types/cup'
import { addBall, awardFrame, undoBall } from '~/utils/cupAdvance'
import { advanceWinner, buildBracket } from '~/utils/cupBracket'
import { CUP_DE_MAX_PLAYERS, CUP_SE_MAX_PLAYERS } from '~/utils/cupLabels'
import { uniqueCupName } from '~/utils/cupNames'

const STORAGE_KEY = 'dautovtech_cup_v1'

const loadWorkspace = (): CupWorkspace => {
  if (typeof window === 'undefined') return createEmptyCupWorkspace()
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return createEmptyCupWorkspace()
    return normalizeCupWorkspace(JSON.parse(raw) as Partial<CupWorkspace | CupState>)
  } catch {
    return createEmptyCupWorkspace()
  }
}

const persist = (workspace: CupWorkspace) => {
  if (typeof window === 'undefined') return
  localStorage.setItem(STORAGE_KEY, JSON.stringify(workspace))
}

const freshShotClock = (sec: number): ShotClockState => ({
  remainingMs: sec * 1000,
  running: false,
  endsAt: null,
  pausedRemainingMs: null
})

export const useCupStore = defineStore('cup', {
  state: (): CupWorkspace => loadWorkspace(),

  getters: {
    activeBundle(state): CupTournamentBundle | null {
      if (!state.activeTournamentId) return null
      return state.tournaments.find((item) => item.tournament.id === state.activeTournamentId) || null
    },

    tournament(state): CupTournamentBundle['tournament'] {
      const bundle = state.tournaments.find((item) => item.tournament.id === state.activeTournamentId)
      return bundle?.tournament ?? createEmptyCupBundle().tournament
    },

    players(state): CupPlayer[] {
      const bundle = state.tournaments.find((item) => item.tournament.id === state.activeTournamentId)
      return bundle?.players ?? []
    },

    matches(state) {
      const bundle = state.tournaments.find((item) => item.tournament.id === state.activeTournamentId)
      return bundle?.matches ?? []
    },

    activeMatchId(state): string | null {
      const bundle = state.tournaments.find((item) => item.tournament.id === state.activeTournamentId)
      return bundle?.activeMatchId ?? null
    },

    shotClock(state): ShotClockState {
      const bundle = state.tournaments.find((item) => item.tournament.id === state.activeTournamentId)
      return bundle?.shotClock ?? createEmptyCupBundle().shotClock
    },

    playerById() {
      return (id: string | null) =>
        id ? this.players.find((player) => player.id === id) || null : null
    },

    matchById() {
      return (id: string) => this.matches.find((match) => match.id === id) || null
    },

    activeMatch() {
      return this.activeMatchId
        ? this.matches.find((match) => match.id === this.activeMatchId) || null
        : null
    },

    readyMatches() {
      return this.matches.filter((match) => match.status === 'ready' || match.status === 'live')
    },

    winnerName() {
      const id = this.tournament.winnerId
      if (!id) return null
      return this.players.find((player) => player.id === id)?.name || null
    },

    hasShotClock(): boolean {
      return this.tournament.shotClockSec > 0
    },

    hasActiveTournament(): boolean {
      const bundle = this.activeBundle
      return Boolean(
        bundle?.tournament.id &&
          (bundle.tournament.status === 'running' || bundle.tournament.status === 'setup')
      )
    },

    tournamentList(state): CupTournamentBundle[] {
      return [...state.tournaments].sort((a, b) =>
        (b.tournament.createdAt || '').localeCompare(a.tournament.createdAt || '')
      )
    },

    runningTournamentCount(state): number {
      return state.tournaments.filter((item) => item.tournament.status === 'running').length
    }
  },

  actions: {
    activeIndex(): number {
      if (!this.activeTournamentId) return -1
      return this.tournaments.findIndex((item) => item.tournament.id === this.activeTournamentId)
    },

    mutateActive(mutator: (bundle: CupTournamentBundle) => void, save = true) {
      const index = this.activeIndex()
      if (index < 0) return
      mutator(this.tournaments[index])
      if (save) persist(this.$state)
    },

    hydrate() {
      Object.assign(this, loadWorkspace())
    },

    persistNow() {
      persist(this.$state)
    },

    resetAll() {
      Object.assign(this, createEmptyCupWorkspace())
      persist(this.$state)
    },

    switchTournament(id: string) {
      if (!this.tournaments.some((item) => item.tournament.id === id)) return
      this.activeTournamentId = id
      persist(this.$state)
    },

    removeTournament(id: string) {
      const index = this.tournaments.findIndex((item) => item.tournament.id === id)
      if (index < 0) return
      this.tournaments.splice(index, 1)
      if (this.activeTournamentId === id) {
        this.activeTournamentId = this.tournaments[0]?.tournament.id ?? null
      }
      persist(this.$state)
    },

    applyRemoteState(partial: Partial<CupState>) {
      const normalized = normalizeCupState(partial)
      if (!normalized.tournament.id) return
      const bundle = cupStateToBundle(normalized)
      const index = this.tournaments.findIndex((item) => item.tournament.id === bundle.tournament.id)
      if (index >= 0) {
        this.tournaments[index] = bundle
      } else {
        this.tournaments.push(bundle)
      }
      this.activeTournamentId = bundle.tournament.id
      persist(this.$state)
    },

    configureSetup(payload: {
      name: string
      format: CupFormat
      raceTo: number
      shotClockSec: number
      playerNames: string[]
      shuffle?: boolean
    }) {
      const players: CupPlayer[] = payload.playerNames
        .map((name) => name.trim())
        .filter(Boolean)
        .map((name, index) => ({
          id: cupUid('p'),
          name,
          seed: index + 1
        }))

      if (players.length < 2) throw new Error('Нужно минимум 2 игрока')
      if (payload.format === 'se' && players.length > CUP_SE_MAX_PLAYERS) {
        throw new Error(`Олимпийская система — до ${CUP_SE_MAX_PLAYERS} игроков`)
      }
      if (payload.format === 'de' && players.length < 3) {
        throw new Error('Система до двух поражений — минимум 3 игрока')
      }
      if (payload.format === 'de' && players.length > CUP_DE_MAX_PLAYERS) {
        throw new Error(`Система до двух поражений — до ${CUP_DE_MAX_PLAYERS} игроков`)
      }

      const built = buildBracket(payload.format, players, { shuffle: Boolean(payload.shuffle) })
      const clockSec = Math.max(0, Number(payload.shotClockSec) || 0)
      const takenNames = this.tournaments.map((item) => item.tournament.name)
      const uniqueName = uniqueCupName(payload.name, takenNames)

      const bundle: CupTournamentBundle = {
        tournament: {
          id: cupUid('t'),
          name: uniqueName,
          format: payload.format,
          raceTo: Math.max(1, payload.raceTo),
          shotClockSec: clockSec,
          status: 'running',
          createdAt: new Date().toISOString(),
          completedAt: null,
          winnerId: null
        },
        players: built.players,
        matches: built.matches,
        activeMatchId:
          built.matches.find((match) => match.status === 'ready')?.id ||
          built.matches.find((match) => match.status === 'live')?.id ||
          null,
        shotClock: freshShotClock(clockSec)
      }

      this.tournaments.push(bundle)
      this.activeTournamentId = bundle.tournament.id
      persist(this.$state)
    },

    setActiveMatch(matchId: string) {
      this.mutateActive((bundle) => {
        bundle.activeMatchId = matchId
        const match = bundle.matches.find((item) => item.id === matchId)
        if (match && match.status === 'ready') match.status = 'live'
        bundle.shotClock = freshShotClock(bundle.tournament.shotClockSec)
      })
    },

    resetShotClock() {
      this.mutateActive((bundle) => {
        bundle.shotClock = freshShotClock(bundle.tournament.shotClockSec)
      })
    },

    startShotClock() {
      if (!this.tournament.shotClockSec) return
      this.mutateActive((bundle) => {
        const clock = bundle.shotClock
        const remaining =
          clock.pausedRemainingMs != null ? clock.pausedRemainingMs : clock.remainingMs
        bundle.shotClock = {
          remainingMs: remaining,
          running: true,
          endsAt: Date.now() + remaining,
          pausedRemainingMs: null
        }
      })
    },

    pauseShotClock() {
      this.mutateActive((bundle) => {
        const clock = bundle.shotClock
        if (!clock.running || !clock.endsAt) return
        const left = Math.max(0, clock.endsAt - Date.now())
        bundle.shotClock = {
          remainingMs: left,
          running: false,
          endsAt: null,
          pausedRemainingMs: left
        }
      })
    },

    tickShotClock() {
      const index = this.activeIndex()
      if (index < 0) return
      const clock = this.tournaments[index].shotClock
      if (!clock.running || !clock.endsAt) return
      const left = Math.max(0, clock.endsAt - Date.now())
      clock.remainingMs = left
      if (left <= 0) {
        clock.running = false
        clock.endsAt = null
        clock.pausedRemainingMs = 0
      }
    },

    addBall(matchId: string, side: 'A' | 'B') {
      this.mutateActive((bundle) => {
        const idx = bundle.matches.findIndex((match) => match.id === matchId)
        if (idx < 0) return
        bundle.matches[idx] = addBall(bundle.matches[idx], side)
        if (bundle.matches[idx].status === 'ready') bundle.matches[idx].status = 'live'
      })
    },

    undoBall(matchId: string, side: 'A' | 'B') {
      this.mutateActive((bundle) => {
        const idx = bundle.matches.findIndex((match) => match.id === matchId)
        if (idx < 0) return
        bundle.matches[idx] = undoBall(bundle.matches[idx], side)
      })
    },

    awardFrame(matchId: string, side: 'A' | 'B') {
      const index = this.activeIndex()
      if (index < 0) return
      const bundle = this.tournaments[index]
      const idx = bundle.matches.findIndex((match) => match.id === matchId)
      if (idx < 0) return
      const result = awardFrame(bundle.matches[idx], side, bundle.tournament.raceTo)
      bundle.matches[idx] = result.match
      bundle.shotClock = freshShotClock(bundle.tournament.shotClockSec)
      if (result.raceWon && result.winnerId) {
        this.completeMatch(matchId, result.winnerId)
        return
      }
      persist(this.$state)
    },

    completeMatch(matchId: string, winnerId: string) {
      this.mutateActive((bundle) => {
        const result = advanceWinner(bundle.matches, matchId, winnerId, bundle.tournament.format)
        bundle.matches = result.matches
        if (result.completed && result.tournamentWinnerId) {
          bundle.tournament.status = 'completed'
          bundle.tournament.winnerId = result.tournamentWinnerId
          bundle.tournament.completedAt = new Date().toISOString()
        }
        bundle.shotClock = freshShotClock(bundle.tournament.shotClockSec)
      })
    },

    exportSnapshot(): CupState {
      const bundle = this.activeBundle
      if (!bundle) return createEmptyCupState()
      return bundleToCupState(bundle)
    }
  }
})
