export type GameMode = 'tournament' | 'casual'
export type PlayerCategory = 1 | 2 | 3
export type PlayerStatus = 'active' | 'eliminated'

export type Player = {
  id: string
  name: string
  category: PlayerCategory
  /** Casual handicap multiplier (e.g. 1.0, 1.5). */
  handicap: number
  startingStack: number
  balance: number
  status: PlayerStatus
}

export type SpecialBall = {
  id: string
  label: string
  /** Multiplier or fixed delta applied to base unit. */
  multiplier: number
  color: string
}

export type RoundConfig = {
  number: number
  durationMinutes: number
  /** Chips each category pays when an opponent scores. */
  tariffs: Record<PlayerCategory, number>
}

export type TableSeat = {
  id: string
  label: string
  playerIds: string[]
}

export type ScoreEvent = {
  id: string
  at: string
  mode: GameMode
  tableId: string
  scorerId: string
  ballId: string
  /** Delta per player id (positive = received). */
  deltas: Record<string, number>
  kind: 'score' | 'penalty' | 'dropout'
  note?: string
}

export type TournamentState = {
  rounds: RoundConfig[]
  currentRoundIndex: number
  tables: TableSeat[]
  tableCount: number
  roundEndsAt: string | null
  timerMuted: boolean
}

export type CasualState = {
  balls: SpecialBall[]
  baseUnit: number
}

export type KolkhozState = {
  version: 1
  mode: GameMode | null
  players: Player[]
  events: ScoreEvent[]
  tournament: TournamentState
  casual: CasualState
  updatedAt: string
}

export const DEFAULT_CASUAL_BALLS: SpecialBall[] = [
  { id: 'standard', label: 'Обычный', multiplier: 1, color: '#f5f5f5' },
  { id: 'yellow', label: 'Жёлтый', multiplier: 2, color: '#eab308' },
  { id: 'red', label: 'Красный', multiplier: 3, color: '#ef4444' },
  { id: 'black', label: 'Чёрный', multiplier: 3, color: '#111827' },
  { id: 'penalty', label: 'Штраф', multiplier: -2, color: '#a855f7' }
]

export const DEFAULT_ROUND: RoundConfig = {
  number: 1,
  durationMinutes: 20,
  tariffs: { 1: 4, 2: 3, 3: 2 }
}

export const createEmptyState = (): KolkhozState => ({
  version: 1,
  mode: null,
  players: [],
  events: [],
  tournament: {
    rounds: [
      { ...DEFAULT_ROUND, number: 1 },
      { number: 2, durationMinutes: 20, tariffs: { 1: 5, 2: 4, 3: 3 } },
      { number: 3, durationMinutes: 15, tariffs: { 1: 6, 2: 5, 3: 4 } }
    ],
    currentRoundIndex: 0,
    tables: [],
    tableCount: 1,
    roundEndsAt: null,
    timerMuted: true
  },
  casual: {
    balls: DEFAULT_CASUAL_BALLS.map((ball) => ({ ...ball })),
    baseUnit: 1
  },
  updatedAt: new Date().toISOString()
})
