export type CupFormat = 'se' | 'de'

export type CupStatus = 'setup' | 'running' | 'completed'

export type MatchStatus = 'pending' | 'ready' | 'live' | 'done'

export type BracketSide = 'winners' | 'losers' | 'final'

export type MatchSlot = 'A' | 'B'

export type CupPlayer = {
  id: string
  name: string
  seed: number
  /** Informational only in v1 (no handicap). */
  category?: 1 | 2 | 3
}

export type CupMatch = {
  id: string
  roundKey: string
  roundLabel: string
  bracketSide: BracketSide
  /** Display order within the round. */
  order: number
  /** Human-readable match number on the grid (#1, #2…). */
  displayNo: number
  playerAId: string | null
  playerBId: string | null
  tableNo: number
  status: MatchStatus
  framesA: number
  framesB: number
  ballsA: number
  ballsB: number
  winnerId: string | null
  /** Where the winner goes. */
  nextMatchId: string | null
  nextSlot: MatchSlot | null
  /** DE: where the loser goes. */
  loserNextMatchId: string | null
  loserNextSlot: MatchSlot | null
}

export type ShotClockState = {
  remainingMs: number
  running: boolean
  endsAt: number | null
  pausedRemainingMs: number | null
}

export type CupState = {
  version: 1
  tournament: {
    id: string
    name: string
    format: CupFormat
    raceTo: number
    /** Seconds per shot; 0 = no shot clock. */
    shotClockSec: number
    status: CupStatus
    createdAt: string
    completedAt: string | null
    winnerId: string | null
  }
  players: CupPlayer[]
  matches: CupMatch[]
  activeMatchId: string | null
  shotClock: ShotClockState
}

/** One tournament without workspace wrapper — used in multi-tournament storage. */
export type CupTournamentBundle = Omit<CupState, 'version'>

export type CupWorkspace = {
  version: 2
  activeTournamentId: string | null
  tournaments: CupTournamentBundle[]
}

export const createEmptyCupBundle = (): CupTournamentBundle => {
  const empty = createEmptyCupState()
  return {
    tournament: { ...empty.tournament },
    players: [],
    matches: [],
    activeMatchId: null,
    shotClock: { ...empty.shotClock }
  }
}

export const createEmptyCupWorkspace = (): CupWorkspace => ({
  version: 2,
  activeTournamentId: null,
  tournaments: []
})

export const bundleToCupState = (bundle: CupTournamentBundle): CupState => ({
  version: 1,
  ...bundle
})

export const cupStateToBundle = (state: CupState): CupTournamentBundle => ({
  tournament: { ...state.tournament },
  players: [...state.players],
  matches: state.matches.map((match) => ({ ...match })),
  activeMatchId: state.activeMatchId,
  shotClock: { ...state.shotClock }
})

export const createEmptyCupState = (): CupState => ({
  version: 1,
  tournament: {
    id: '',
    name: '',
    format: 'se',
    raceTo: 5,
    shotClockSec: 0,
    status: 'setup',
    createdAt: '',
    completedAt: null,
    winnerId: null
  },
  players: [],
  matches: [],
  activeMatchId: null,
  shotClock: {
    remainingMs: 0,
    running: false,
    endsAt: null,
    pausedRemainingMs: null
  }
})

export const normalizeCupBundle = (
  partial: Partial<CupTournamentBundle> | null | undefined
): CupTournamentBundle => {
  const empty = createEmptyCupBundle()
  if (!partial) return empty
  return {
    tournament: {
      ...empty.tournament,
      ...(partial.tournament || {})
    },
    players: Array.isArray(partial.players) ? partial.players : [],
    matches: Array.isArray(partial.matches)
      ? partial.matches.map((match, index) => ({
          ...match,
          roundKey: match.roundKey === 'grand-final' ? 'de-final' : match.roundKey,
          roundLabel:
            match.roundKey === 'grand-final' || match.roundLabel === 'Большой финал'
              ? 'Финал'
              : match.roundLabel,
          displayNo: match.displayNo || index + 1
        }))
      : [],
    activeMatchId: partial.activeMatchId ?? null,
    shotClock: {
      ...empty.shotClock,
      ...(partial.shotClock || {})
    }
  }
}

export const normalizeCupState = (partial: Partial<CupState> | null | undefined): CupState => {
  if (!partial || partial.version !== 1) {
    return createEmptyCupState()
  }
  return bundleToCupState(normalizeCupBundle(partial))
}

export const normalizeCupWorkspace = (
  partial: Partial<CupWorkspace | CupState> | null | undefined
): CupWorkspace => {
  if (!partial || typeof partial !== 'object') return createEmptyCupWorkspace()

  if (partial.version === 2) {
    const workspace = partial as Partial<CupWorkspace>
    const tournaments = Array.isArray(workspace.tournaments)
      ? workspace.tournaments.map((item) => normalizeCupBundle(item))
      : []
    const activeTournamentId =
      workspace.activeTournamentId &&
      tournaments.some((item) => item.tournament.id === workspace.activeTournamentId)
        ? workspace.activeTournamentId
        : tournaments[0]?.tournament.id ?? null
    return {
      version: 2,
      activeTournamentId,
      tournaments
    }
  }

  if (partial.version === 1) {
    const bundle = normalizeCupBundle(partial as Partial<CupTournamentBundle>)
    if (!bundle.tournament.id) return createEmptyCupWorkspace()
    return {
      version: 2,
      activeTournamentId: bundle.tournament.id,
      tournaments: [bundle]
    }
  }

  return createEmptyCupWorkspace()
}

export const nextPowerOfTwo = (n: number) => {
  let p = 1
  while (p < n) p *= 2
  return p
}

export const cupUid = (prefix = 'c') =>
  typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
