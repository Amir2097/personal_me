export type GameMode = 'tournament' | 'casual'
/** Detailed = chip scoring per ball; Organizer = seating/timer management only. */
export type TournamentKind = 'detailed' | 'organizer'
export type PlayerCategory = 1 | 2 | 3
export type PlayerStatus = 'active' | 'eliminated'
export type BuyInKind = 'entry' | 'rebuy' | 'addon'

export type Player = {
  id: string
  name: string
  category: PlayerCategory
  /** Casual handicap in whole balls (e.g. +2 for a beginner). */
  handicap: number
  /** Personal ball stake (₽) for casual; defaults to table ballPrice. */
  stakePrice?: number
  startingStack: number
  balance: number
  status: PlayerStatus
}

export type CasualBallPartyRole = 'rack' | 'extra'

export type SpecialBall = {
  id: string
  label: string
  /** Price in table currency (₽). */
  price: number
  color: string
  /**
   * rack — в зачёт 16 шаров пирамиды (занимает слот, можно вместо обычного).
   * extra — дополнительно к 16, не двигает счётчик пирамиды.
   */
  partyRole: CasualBallPartyRole
  /** @deprecated Migrated to price on load. */
  multiplier?: number
}

export type RoundConfig = {
  number: number
  durationMinutes: number
  /** Chips each category pays / stake markup for the round. */
  tariffs: Record<PlayerCategory, number>
}

export type TableSeat = {
  id: string
  /** Physical hall table number shown to players (e.g. 3, 7, 12). */
  number: number
  label: string
  playerIds: string[]
}

export type ScoreEventKind =
  | 'score'
  | 'penalty'
  | 'dropout'
  | 'fine_place'
  | 'fine_claim'
  | 'fine_return'
  | 'party_settle'
  | 'session_end'
  | 'casual_foul'

export type ScoreEvent = {
  id: string
  at: string
  mode: GameMode
  tableId: string
  scorerId: string
  ballId: string
  /** Delta per player id (positive = received). */
  deltas: Record<string, number>
  kind: ScoreEventKind
  note?: string
  /** Chips moved via table pot (общак). */
  potAmount?: number
  /** Snapshot of pot before claim/return (for undo). */
  potSnapshot?: TablePot
  /** Snapshot for undo after party settlement. */
  partySnapshot?: {
    playerOrder: string[]
    party: CasualPartyState
  }
  /** Casual party pot metadata (for undo). */
  partyBallIndex?: number
  partyPointsDelta?: number
  partyPointRole?: CasualBallPartyRole
  /** Final balances snapshot on session end. */
  sessionBalances?: Record<string, number>
  /** Casual foul undo snapshot. */
  foulSnapshot?: {
    party: CasualPartyState
    playerBalances?: Record<string, number>
  }
}

export type TablePotContribution = {
  playerId: string
  amount: number
}

/** Open fine pot on a table — chips sit in общак until claimed or returned. */
export type TablePot = {
  id: string
  tableId: string
  amount: number
  contributions: TablePotContribution[]
  circlePlayerIds: string[]
  createdAt: string
  /** Circle completes when pass cursor returns to this player without a score. */
  returnAtPlayerId: string
  /** Whose «мимо» is expected next for auto-return. */
  passCursorPlayerId: string
}

export type BuyInPreset = {
  money: number
  chips: number
}

export type PrizePlace = {
  place: number
  /** Share of prize pool, percent. */
  percent: number
}

export type BuyInRecord = {
  id: string
  at: string
  playerId: string
  kind: BuyInKind
  money: number
  chips: number
  note?: string
  roundNumber?: number
}

export type BankState = {
  /** Percent of bank that goes to prizes (typically 80). */
  prizePercent: number
  currencyLabel: string
  entryPreset: BuyInPreset
  rebuyPreset: BuyInPreset
  addonPreset: BuyInPreset
  prizePlaces: PrizePlace[]
}

export type TournamentState = {
  kind: TournamentKind
  rounds: RoundConfig[]
  currentRoundIndex: number
  tables: TableSeat[]
  tableCount: number
  roundEndsAt: string | null
  /** When paused, remaining ms until round end (timer stopped). */
  timerPausedRemainingMs: number | null
  timerMuted: boolean
  bank: BankState
  buyIns: BuyInRecord[]
  /** Open fine pots (общак) per table. */
  pots: TablePot[]
}

export type CasualPenaltyMode = 'pay_all' | 'ball_from_home' | 'pass_advantage'

export type CasualPenaltyConfig = {
  mode: CasualPenaltyMode
  /** pay_all: charge each opponent the offender's personal stake. */
  usePersonalStake: boolean
}

export type CasualPartyState = {
  number: number
  /** Last rack ball index in this party (0 = rack not started). */
  ballIndex: number
  /** Rack tally toward 16 (by player). */
  rackPointsByPlayer: Record<string, number>
  /** Extra balls outside the rack 16 (by player). */
  extraPointsByPlayer: Record<string, number>
  /** Sum of rack points in the open party. */
  rackPointsTotal: number
  /** Balls returned to the table (ball_from_home fouls). */
  ballsOnTable: number
  /** Owed ball placements after a foul with zero potted balls. */
  ballDebtByPlayer: Record<string, number>
  /** Next player with a pending free shot (pass_advantage). */
  freeShotForPlayerId: string | null
  startedAt: string
}

export type CasualState = {
  /** Base table stake per scoring unit (₽). */
  ballPrice: number
  currencyLabel: string
  balls: SpecialBall[]
  penalties: CasualPenaltyConfig
  /** Current open party; null until first ball or explicit start. */
  party: CasualPartyState | null
  /** Set when the whole meeting is closed with final tally. */
  sessionEndedAt: string | null
  /** @deprecated Use ballPrice. */
  baseUnit?: number
}

export const DEFAULT_CASUAL_PENALTIES: CasualPenaltyConfig = {
  mode: 'pay_all',
  usePersonalStake: true
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
  { id: 'standard', label: 'Обычный', price: 100, color: '#f5f5f5', partyRole: 'rack' },
  { id: 'yellow', label: 'Жёлтый', price: 200, color: '#eab308', partyRole: 'rack' },
  { id: 'red', label: 'Красный', price: 300, color: '#ef4444', partyRole: 'rack' },
  { id: 'black', label: 'Чёрный', price: 300, color: '#111827', partyRole: 'rack' }
]

export const normalizeCasualBall = (ball: Partial<SpecialBall>, tableBallPrice: number): SpecialBall => ({
  id: ball.id || uid(),
  label: ball.label || 'Шар',
  color: ball.color || '#94a3b8',
  partyRole: ball.partyRole === 'extra' ? 'extra' : 'rack',
  price:
    typeof ball.price === 'number'
      ? ball.price
      : typeof ball.multiplier === 'number'
        ? Math.round(tableBallPrice * ball.multiplier)
        : tableBallPrice
})

const uid = () =>
  typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `ball_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`

export const normalizeCasualParty = (party: Partial<CasualPartyState> & { pointsByPlayer?: Record<string, number> }): CasualPartyState => {
  const baseFields = {
    ballsOnTable: party.ballsOnTable || 0,
    ballDebtByPlayer: { ...(party.ballDebtByPlayer || {}) },
    freeShotForPlayerId: party.freeShotForPlayerId ?? null
  }

  if (party.rackPointsByPlayer) {
    return {
      number: party.number || 1,
      ballIndex: party.ballIndex || 0,
      rackPointsByPlayer: { ...party.rackPointsByPlayer },
      extraPointsByPlayer: { ...(party.extraPointsByPlayer || {}) },
      rackPointsTotal:
        typeof party.rackPointsTotal === 'number'
          ? party.rackPointsTotal
          : Object.values(party.rackPointsByPlayer).reduce((sum, value) => sum + value, 0),
      startedAt: party.startedAt || new Date().toISOString(),
      ...baseFields
    }
  }

  const legacy = party.pointsByPlayer || {}
  const rackTotal = Object.values(legacy).reduce((sum, value) => sum + value, 0)
  return {
    number: party.number || 1,
    ballIndex: party.ballIndex || 0,
    rackPointsByPlayer: { ...legacy },
    extraPointsByPlayer: {},
    rackPointsTotal: rackTotal,
    startedAt: party.startedAt || new Date().toISOString(),
    ...baseFields
  }
}

export const DEFAULT_ROUND: RoundConfig = {
  number: 1,
  durationMinutes: 20,
  tariffs: { 1: 4, 2: 3, 3: 2 }
}

export const DEFAULT_BANK: BankState = {
  prizePercent: 80,
  currencyLabel: '₽',
  entryPreset: { money: 500, chips: 20 },
  rebuyPreset: { money: 500, chips: 20 },
  addonPreset: { money: 500, chips: 50 },
  prizePlaces: [
    { place: 1, percent: 50 },
    { place: 2, percent: 30 },
    { place: 3, percent: 20 }
  ]
}

export const createEmptyState = (): KolkhozState => ({
  version: 1,
  mode: null,
  players: [],
  events: [],
  tournament: {
    kind: 'detailed',
    rounds: [
      { ...DEFAULT_ROUND, number: 1 },
      { number: 2, durationMinutes: 20, tariffs: { 1: 5, 2: 4, 3: 3 } },
      { number: 3, durationMinutes: 15, tariffs: { 1: 6, 2: 5, 3: 4 } }
    ],
    currentRoundIndex: 0,
    tables: [],
    tableCount: 1,
    roundEndsAt: null,
    timerPausedRemainingMs: null,
    timerMuted: false,
    bank: { ...DEFAULT_BANK, entryPreset: { ...DEFAULT_BANK.entryPreset }, rebuyPreset: { ...DEFAULT_BANK.rebuyPreset }, addonPreset: { ...DEFAULT_BANK.addonPreset }, prizePlaces: DEFAULT_BANK.prizePlaces.map((p) => ({ ...p })) },
    buyIns: [],
    pots: []
  },
  casual: {
    ballPrice: 100,
    currencyLabel: '₽',
    balls: DEFAULT_CASUAL_BALLS.map((ball) => ({ ...ball })),
    penalties: { ...DEFAULT_CASUAL_PENALTIES },
    party: null,
    sessionEndedAt: null
  },
  updatedAt: new Date().toISOString()
})

/** Merge saved localStorage with defaults (older saves may miss new fields). */
export const normalizeState = (parsed: Partial<KolkhozState>): KolkhozState => {
  const base = createEmptyState()
  const parsedBank = parsed.tournament?.bank
  const bank: BankState = {
    ...base.tournament.bank,
    ...(parsedBank || {}),
    entryPreset: { ...base.tournament.bank.entryPreset, ...(parsedBank?.entryPreset || {}) },
    rebuyPreset: { ...base.tournament.bank.rebuyPreset, ...(parsedBank?.rebuyPreset || {}) },
    addonPreset: { ...base.tournament.bank.addonPreset, ...(parsedBank?.addonPreset || {}) },
    prizePlaces:
      parsedBank?.prizePlaces?.length
        ? parsedBank.prizePlaces.map((p) => ({ ...p }))
        : base.tournament.bank.prizePlaces.map((p) => ({ ...p }))
  }

  const tournament = {
    ...base.tournament,
    ...(parsed.tournament || {}),
    kind: (parsed.tournament?.kind === 'organizer' ? 'organizer' : 'detailed') as TournamentKind,
    timerPausedRemainingMs: parsed.tournament?.timerPausedRemainingMs ?? null,
    rounds: parsed.tournament?.rounds?.length ? parsed.tournament.rounds : base.tournament.rounds,
    bank,
    buyIns: Array.isArray(parsed.tournament?.buyIns) ? parsed.tournament!.buyIns : [],
    pots: (Array.isArray(parsed.tournament?.pots) ? parsed.tournament!.pots : []).map((raw) => {
      const pot = raw as TablePot
      const contributions = Array.isArray(pot.contributions)
        ? pot.contributions.map((item) => ({ ...item }))
        : []
      const circlePlayerIds = pot.circlePlayerIds?.length
        ? [...pot.circlePlayerIds]
        : contributions.map((item) => item.playerId)
      const returnAtPlayerId = pot.returnAtPlayerId || contributions[0]?.playerId || ''
      const passCursorPlayerId = pot.passCursorPlayerId || circlePlayerIds.find((id) => id !== returnAtPlayerId) || returnAtPlayerId
      return {
        id: pot.id,
        tableId: pot.tableId,
        amount: Number(pot.amount) || 0,
        contributions,
        circlePlayerIds,
        createdAt: pot.createdAt || new Date().toISOString(),
        returnAtPlayerId,
        passCursorPlayerId
      } satisfies TablePot
    }),
    tables: (parsed.tournament?.tables || []).map((table, index) => ({
      id: table.id,
      number: typeof table.number === 'number' && table.number > 0 ? table.number : index + 1,
      label: table.label || `Стол №${typeof table.number === 'number' && table.number > 0 ? table.number : index + 1}`,
      playerIds: table.playerIds || []
    }))
  }
  return {
    ...base,
    ...parsed,
    version: 1,
    tournament,
    casual: {
      ...base.casual,
      ...(parsed.casual || {}),
      ballPrice:
        parsed.casual?.ballPrice ??
        parsed.casual?.baseUnit ??
        base.casual.ballPrice,
      currencyLabel: parsed.casual?.currencyLabel ?? base.casual.currencyLabel,
      balls: (parsed.casual?.balls?.length ? parsed.casual.balls : base.casual.balls)
        .filter((ball) => ball.id !== 'penalty')
        .map((ball) =>
          normalizeCasualBall(ball, parsed.casual?.ballPrice ?? parsed.casual?.baseUnit ?? base.casual.ballPrice)
        ),
      penalties: {
        ...DEFAULT_CASUAL_PENALTIES,
        ...(parsed.casual?.penalties || {}),
        mode:
          parsed.casual?.penalties?.mode === 'ball_from_home' ||
          parsed.casual?.penalties?.mode === 'pass_advantage'
            ? parsed.casual.penalties.mode
            : 'pay_all',
        usePersonalStake: parsed.casual?.penalties?.usePersonalStake ?? true
      },
      party: parsed.casual?.party
        ? normalizeCasualParty(parsed.casual.party)
        : null,
      sessionEndedAt: parsed.casual?.sessionEndedAt ?? null
    },
    players: parsed.players || [],
    events: parsed.events || []
  }
}
