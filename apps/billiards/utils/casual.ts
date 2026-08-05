import type { CasualBallPartyRole, CasualPartyState, Player, ScoreEvent, SpecialBall } from '~/types/kolkhoz'
import { normalizeCasualParty } from '~/types/kolkhoz'

/** Total scoring points in a full rack (14 regular + last ball ×2). */
export const CASUAL_PARTY_TARGET_POINTS = 16

/** Physical rack balls per party. */
export const CASUAL_PARTY_BALL_COUNT = 15

const uid = () =>
  typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `id_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`

export const createCasualParty = (number: number): CasualPartyState => ({
  number,
  ballIndex: 0,
  rackPointsByPlayer: {},
  extraPointsByPlayer: {},
  rackPointsTotal: 0,
  ballsOnTable: 0,
  ballDebtByPlayer: {},
  freeShotForPlayerId: null,
  startedAt: new Date().toISOString()
})

export const ballPartyRole = (ball: SpecialBall): CasualBallPartyRole =>
  ball.partyRole === 'extra' ? 'extra' : 'rack'

/** Points awarded for the given physical rack ball index (1-based, 15 = last ×2). */
export const ballPointsForIndex = (ballIndex: number): number =>
  ballIndex >= CASUAL_PARTY_BALL_COUNT ? 2 : 1

export const ballPriceOf = (ball: SpecialBall, tableBallPrice: number): number => {
  if (typeof ball.price === 'number' && Number.isFinite(ball.price)) return ball.price
  if (typeof ball.multiplier === 'number') return tableBallPrice * ball.multiplier
  return tableBallPrice
}

/** Rack tally for one potted ball (price can weigh more than the base stake). */
export const rackPointsForPot = (
  physicalIndex: number,
  ball: SpecialBall,
  tableBallPrice: number
): number => {
  const base = ballPointsForIndex(physicalIndex)
  const price = ballPriceOf(ball, tableBallPrice)
  if (tableBallPrice <= 0) return base
  return base * (price / tableBallPrice)
}

/** Extra ball tally — outside the rack 16. */
export const extraPointsForPot = (ball: SpecialBall, tableBallPrice: number): number => {
  const price = ballPriceOf(ball, tableBallPrice)
  if (tableBallPrice <= 0) return price >= 0 ? 1 : -1
  return price / tableBallPrice
}

export const playerRackPoints = (party: CasualPartyState, playerId: string): number =>
  party.rackPointsByPlayer[playerId] || 0

export const playerExtraPoints = (party: CasualPartyState, playerId: string): number =>
  party.extraPointsByPlayer[playerId] || 0

export const playerPartyPoints = (party: CasualPartyState, playerId: string): number =>
  playerRackPoints(party, playerId) + playerExtraPoints(party, playerId)

export const partyPointsTotal = (party: CasualPartyState): number =>
  party.rackPointsTotal + Object.values(party.extraPointsByPlayer).reduce((sum, value) => sum + value, 0)

export const partyNorm = (party: CasualPartyState, playerCount: number): number => {
  if (playerCount <= 0) return 0
  const rackTotal = party.rackPointsTotal
  if (rackTotal <= 0) return CASUAL_PARTY_TARGET_POINTS / playerCount
  return rackTotal / playerCount
}

export const partyTargetNorm = (playerCount: number): number =>
  playerCount > 0 ? CASUAL_PARTY_TARGET_POINTS / playerCount : 0

export const isRackComplete = (party: CasualPartyState): boolean =>
  party.rackPointsTotal >= CASUAL_PARTY_TARGET_POINTS

/** @deprecated Use isRackComplete */
export const isPartyComplete = isRackComplete

export const nextBallIndex = (party: CasualPartyState): number => party.ballIndex + 1

export const isLastBall = (ballIndex: number): boolean => ballIndex >= CASUAL_PARTY_BALL_COUNT

export const casualHandicapBalls = (player: Player): number =>
  Math.max(0, Math.round(Number(player.handicap) || 0))

export const effectivePartyScore = (party: CasualPartyState, player: Player): number =>
  playerPartyPoints(party, player.id) + casualHandicapBalls(player)

export const shouldUseNormSettlement = (players: Player[], playerIds: string[]): boolean => {
  if (playerIds.length <= 0) return false
  if (CASUAL_PARTY_TARGET_POINTS % playerIds.length !== 0) return false
  return playerIds.every((id) => {
    const player = players.find((item) => item.id === id)
    return player ? casualHandicapBalls(player) === 0 : true
  })
}

export const rotatePlayerOrder = (players: Player[]): Player[] => {
  const active = players.filter((player) => player.status === 'active')
  const inactive = players.filter((player) => player.status !== 'active')
  if (active.length < 2) return players
  const [first, ...rest] = active
  return [...rest, first!, ...inactive]
}

export type PartySettlementLine = {
  playerId: string
  rackPoints: number
  extraPoints: number
  points: number
  handicap: number
  effective: number
  norm: number
  deltaPoints: number
  deltaMoney: number
  method: 'norm' | 'pairwise'
}

const buildLines = (
  party: CasualPartyState,
  players: Player[],
  playerIds: string[],
  ballPrice: number,
  method: 'norm' | 'pairwise'
): PartySettlementLine[] => {
  const effectiveById = Object.fromEntries(
    playerIds.map((id) => {
      const player = players.find((item) => item.id === id)!
      return [id, effectivePartyScore(party, player)]
    })
  )

  if (method === 'norm') {
    const norm = partyNorm(party, playerIds.length)
    return playerIds.map((playerId) => {
      const player = players.find((item) => item.id === playerId)!
      const rackPoints = playerRackPoints(party, playerId)
      const extraPoints = playerExtraPoints(party, playerId)
      const points = rackPoints + extraPoints
      const effective = effectiveById[playerId] ?? 0
      const deltaPoints = effective - norm
      return {
        playerId,
        rackPoints,
        extraPoints,
        points,
        handicap: casualHandicapBalls(player),
        effective,
        norm,
        deltaPoints,
        deltaMoney: Math.round(deltaPoints * ballPrice),
        method
      }
    })
  }

  const deltas: Record<string, number> = Object.fromEntries(playerIds.map((id) => [id, 0]))
  for (let i = 0; i < playerIds.length; i += 1) {
    for (let j = i + 1; j < playerIds.length; j += 1) {
      const leftId = playerIds[i]!
      const rightId = playerIds[j]!
      const diff = (effectiveById[leftId] ?? 0) - (effectiveById[rightId] ?? 0)
      const money = Math.round(diff * ballPrice)
      deltas[leftId] = (deltas[leftId] ?? 0) + money
      deltas[rightId] = (deltas[rightId] ?? 0) - money
    }
  }

  return playerIds.map((playerId) => {
    const player = players.find((item) => item.id === playerId)!
    const rackPoints = playerRackPoints(party, playerId)
    const extraPoints = playerExtraPoints(party, playerId)
    const points = rackPoints + extraPoints
    const effective = effectiveById[playerId] ?? 0
    return {
      playerId,
      rackPoints,
      extraPoints,
      points,
      handicap: casualHandicapBalls(player),
      effective,
      norm: 0,
      deltaPoints: effective,
      deltaMoney: deltas[playerId] ?? 0,
      method
    }
  })
}

export const calcPartySettlement = (
  party: CasualPartyState,
  players: Player[],
  playerIds: string[],
  ballPrice: number
): PartySettlementLine[] => {
  const method = shouldUseNormSettlement(players, playerIds) ? 'norm' : 'pairwise'
  return buildLines(party, players, playerIds, ballPrice, method)
}

export const applyMoneyDeltas = (players: Player[], deltas: Record<string, number>): Player[] =>
  players.map((player) => {
    if (!(player.id in deltas)) return player
    return { ...player, balance: player.balance + deltas[player.id]! }
  })

export type PotCasualBallResult = {
  party: CasualPartyState
  event: ScoreEvent
  points: number
  ballIndex: number | null
  partyRole: CasualBallPartyRole
}

export const potCasualBall = (
  party: CasualPartyState,
  ball: SpecialBall,
  tableBallPrice: number,
  tablePlayerIds: string[],
  scorerId: string,
  tableId: string,
  previousName: string
): PotCasualBallResult => {
  const role = ballPartyRole(ball)
  const price = ballPriceOf(ball, tableBallPrice)

  const debt = party.ballDebtByPlayer[scorerId] || 0
  if (role === 'rack' && debt > 0) {
    const nextDebt = { ...party.ballDebtByPlayer }
    nextDebt[scorerId] = debt - 1
    if (nextDebt[scorerId] <= 0) delete nextDebt[scorerId]
    const nextParty: CasualPartyState = {
      ...party,
      ballDebtByPlayer: nextDebt,
      ballsOnTable: (party.ballsOnTable || 0) + 1,
      freeShotForPlayerId: party.freeShotForPlayerId === scorerId ? null : party.freeShotForPlayerId
    }
    return {
      party: nextParty,
      points: 0,
      ballIndex: null,
      partyRole: 'rack',
      event: {
        id: uid(),
        at: new Date().toISOString(),
        mode: 'casual',
        tableId,
        scorerId,
        ballId: 'ball-debt',
        deltas: {},
        kind: 'score',
        note: `Выставил шар в счёт долга · vs ${previousName}`
      }
    }
  }

  if (role === 'extra') {
    const points = extraPointsForPot(ball, tableBallPrice)
    const nextParty: CasualPartyState = {
      ...party,
      extraPointsByPlayer: {
        ...party.extraPointsByPlayer,
        [scorerId]: (party.extraPointsByPlayer[scorerId] || 0) + points
      },
      freeShotForPlayerId: party.freeShotForPlayerId === scorerId ? null : party.freeShotForPlayerId
    }

    return {
      party: nextParty,
      points,
      ballIndex: null,
      partyRole: 'extra',
      event: {
        id: uid(),
        at: new Date().toISOString(),
        mode: 'casual',
        tableId,
        scorerId,
        ballId: ball.id,
        deltas: {},
        kind: price < 0 ? 'penalty' : 'score',
        note: `${ball.label} · доп. · ${price} ₽ · vs ${previousName}`,
        partyPointsDelta: points,
        partyPointRole: 'extra'
      }
    }
  }

  const ballIndex = nextBallIndex(party)
  if (ballIndex > CASUAL_PARTY_BALL_COUNT) {
    throw new Error('Все шары пирамиды уже учтены. Закройте партию или отметьте шар как «дополнительный».')
  }

  const points = rackPointsForPot(ballIndex, ball, tableBallPrice)
  const nextParty: CasualPartyState = {
    ...party,
    ballIndex,
    rackPointsTotal: party.rackPointsTotal + points,
    rackPointsByPlayer: {
      ...party.rackPointsByPlayer,
      [scorerId]: (party.rackPointsByPlayer[scorerId] || 0) + points
    },
    freeShotForPlayerId: party.freeShotForPlayerId === scorerId ? null : party.freeShotForPlayerId
  }

  const weightNote = price !== tableBallPrice ? ` · ${price} ₽` : ''

  return {
    party: nextParty,
    points,
    ballIndex,
    partyRole: 'rack',
    event: {
      id: uid(),
      at: new Date().toISOString(),
      mode: 'casual',
      tableId,
      scorerId,
      ballId: ball.id,
      deltas: {},
      kind: price < 0 ? 'penalty' : 'score',
      note: `${ball.label} · пирамида ${ballIndex}${isLastBall(ballIndex) ? ' (×2)' : ''}${weightNote} · vs ${previousName}`,
      partyBallIndex: ballIndex,
      partyPointsDelta: points,
      partyPointRole: 'rack'
    }
  }
}

export type SettleCasualPartyResult = {
  players: Player[]
  party: CasualPartyState
  event: ScoreEvent
  lines: PartySettlementLine[]
}

export const settleCasualParty = (
  party: CasualPartyState,
  players: Player[],
  tablePlayerIds: string[],
  ballPrice: number,
  tableId: string
): SettleCasualPartyResult => {
  const activeIds = tablePlayerIds.filter((id) => {
    const player = players.find((item) => item.id === id)
    return player && player.status === 'active'
  })
  if (activeIds.length < 2) {
    throw new Error('Нужно минимум 2 игрока для закрытия партии.')
  }

  const total = partyPointsTotal(party)
  if (total <= 0) {
    throw new Error('В партии ещё нет забитых шаров.')
  }

  const lines = calcPartySettlement(party, players, activeIds, ballPrice)
  const deltas = Object.fromEntries(lines.map((line) => [line.playerId, line.deltaMoney]))
  const method = lines[0]?.method ?? 'pairwise'
  const norm = lines[0]?.norm ?? 0

  const orderBefore = players.map((player) => player.id)
  const rotated = rotatePlayerOrder(players)
  const nextParty = createCasualParty(party.number + 1)

  const note =
    method === 'norm'
      ? `Партия ${party.number}: норма ${norm.toFixed(2)} шар.`
      : `Партия ${party.number}: попарный расчёт с форой.`

  return {
    players: applyMoneyDeltas(rotated, deltas),
    party: nextParty,
    lines,
    event: {
      id: uid(),
      at: new Date().toISOString(),
      mode: 'casual',
      tableId,
      scorerId: activeIds[0]!,
      ballId: 'party-settle',
      deltas,
      kind: 'party_settle',
      note,
      partySnapshot: {
        playerOrder: orderBefore,
        party: normalizeCasualParty(party)
      }
    }
  }
}

export const hasOpenPartyActivity = (party: CasualPartyState | null): boolean =>
  Boolean(party && partyPointsTotal(party) > 0)
