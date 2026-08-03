import type {
  CasualState,
  GameMode,
  Player,
  PlayerCategory,
  RoundConfig,
  ScoreEvent,
  SpecialBall
} from '~/types/kolkhoz'

const uid = () =>
  typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `id_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`

export type ProcessScoreInput = {
  mode: GameMode
  players: Player[]
  tableId: string
  scorerId: string
  ballId: string
  round?: RoundConfig
  casual?: CasualState
  kind?: 'score' | 'penalty'
}

export type ProcessScoreResult = {
  players: Player[]
  event: ScoreEvent
}

/** Active players in seating order (tablePlayerIds). */
export const orderedActiveOnTable = (players: Player[], tablePlayerIds: string[]) =>
  tablePlayerIds
    .map((id) => players.find((player) => player.id === id))
    .filter((player): player is Player => Boolean(player && player.status === 'active'))

/**
 * Previous player in the circle (who the scorer "beats").
 * Order follows table seating / join order.
 */
export const previousPlayerId = (orderedIds: string[], scorerId: string): string | null => {
  if (orderedIds.length < 2) return null
  const index = orderedIds.indexOf(scorerId)
  if (index < 0) return null
  const prevIndex = (index - 1 + orderedIds.length) % orderedIds.length
  return orderedIds[prevIndex] ?? null
}

const applyDeltas = (players: Player[], deltas: Record<string, number>) =>
  players.map((player) => {
    if (!(player.id in deltas)) return player
    return { ...player, balance: player.balance + deltas[player.id]! }
  })

export const processTournamentScore = (
  players: Player[],
  tablePlayerIds: string[],
  scorerId: string,
  round: RoundConfig,
  tableId: string,
  ballId = 'standard',
  kind: 'score' | 'penalty' = 'score'
): ProcessScoreResult => {
  const active = orderedActiveOnTable(players, tablePlayerIds)
  const orderedIds = active.map((player) => player.id)
  const scorer = active.find((player) => player.id === scorerId)
  if (!scorer) {
    throw new Error('Scorer not found among active players at this table.')
  }

  const targetId = previousPlayerId(orderedIds, scorerId)
  if (!targetId) {
    throw new Error('Need at least 2 active players to score.')
  }
  const target = active.find((player) => player.id === targetId)!
  const tariff = round.tariffs[target.category as PlayerCategory] ?? 0
  const paid = kind === 'penalty' ? -tariff : tariff

  const deltas: Record<string, number> = {
    [targetId]: -paid,
    [scorerId]: paid
  }

  return {
    players: applyDeltas(players, deltas),
    event: {
      id: uid(),
      at: new Date().toISOString(),
      mode: 'tournament',
      tableId,
      scorerId,
      ballId,
      deltas,
      kind,
      note: `vs ${target.name}`
    }
  }
}

export const processCasualScore = (
  players: Player[],
  tablePlayerIds: string[],
  scorerId: string,
  ball: SpecialBall,
  baseUnit: number,
  tableId: string,
  kind: 'score' | 'penalty' = 'score'
): ProcessScoreResult => {
  const active = orderedActiveOnTable(players, tablePlayerIds)
  const orderedIds = active.map((player) => player.id)
  const scorer = active.find((player) => player.id === scorerId)
  if (!scorer) {
    throw new Error('Scorer not found among active players at this table.')
  }

  const targetId = previousPlayerId(orderedIds, scorerId)
  if (!targetId) {
    throw new Error('Need at least 2 active players to score.')
  }
  const target = active.find((player) => player.id === targetId)!

  const sign = kind === 'penalty' || ball.multiplier < 0 ? -1 : 1
  const absMultiplier = Math.abs(ball.multiplier)
  // Amount based on the previous player's handicap (how much they owe when beaten).
  const amount = baseUnit * absMultiplier * target.handicap * sign

  const deltas: Record<string, number> = {
    [targetId]: -amount,
    [scorerId]: amount
  }

  return {
    players: applyDeltas(players, deltas),
    event: {
      id: uid(),
      at: new Date().toISOString(),
      mode: 'casual',
      tableId,
      scorerId,
      ballId: ball.id,
      deltas,
      kind: ball.multiplier < 0 || kind === 'penalty' ? 'penalty' : 'score',
      note: `vs ${target.name}`
    }
  }
}

export const processScore = (input: ProcessScoreInput & { tablePlayerIds: string[] }): ProcessScoreResult => {
  if (input.mode === 'tournament') {
    if (!input.round) throw new Error('Round config required for tournament scoring.')
    return processTournamentScore(
      input.players,
      input.tablePlayerIds,
      input.scorerId,
      input.round,
      input.tableId,
      input.ballId,
      input.kind
    )
  }

  if (!input.casual) throw new Error('Casual config required for casual scoring.')
  const ball = input.casual.balls.find((item) => item.id === input.ballId)
  if (!ball) throw new Error(`Unknown ball: ${input.ballId}`)
  return processCasualScore(
    input.players,
    input.tablePlayerIds,
    input.scorerId,
    ball,
    input.casual.baseUnit,
    input.tableId,
    input.kind
  )
}

export const applyDropout = (
  players: Player[],
  playerId: string,
  tableId: string
): { players: Player[]; event: ScoreEvent } => {
  const nextPlayers = players.map((player) =>
    player.id === playerId ? { ...player, status: 'eliminated' as const } : player
  )
  return {
    players: nextPlayers,
    event: {
      id: uid(),
      at: new Date().toISOString(),
      mode: 'tournament',
      tableId,
      scorerId: playerId,
      ballId: 'dropout',
      deltas: {},
      kind: 'dropout',
      note: 'Player eliminated'
    }
  }
}

export const undoEvent = (players: Player[], event: ScoreEvent): Player[] => {
  if (event.kind === 'dropout') {
    return players.map((player) =>
      player.id === event.scorerId ? { ...player, status: 'active' as const } : player
    )
  }
  return players.map((player) => {
    const delta = event.deltas[player.id]
    if (delta === undefined) return player
    return { ...player, balance: player.balance - delta }
  })
}

export const totalBalance = (players: Player[]) =>
  players.reduce((sum, player) => sum + player.balance, 0)
