import type { Player, ScoreEvent, TablePot } from '~/types/kolkhoz'
import { orderedActiveOnTable } from '~/utils/scoring'

const uid = () =>
  typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `pot_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`

const applyDeltas = (players: Player[], deltas: Record<string, number>) =>
  players.map((player) => {
    if (!(player.id in deltas)) return player
    return { ...player, balance: player.balance + deltas[player.id]! }
  })

export const potForTable = (pots: TablePot[], tableId: string) =>
  pots.find((pot) => pot.tableId === tableId) ?? null

const clonePot = (pot: TablePot): TablePot => ({
  ...pot,
  contributions: pot.contributions.map((item) => ({ ...item })),
  circlePlayerIds: [...pot.circlePlayerIds]
})

/** Next active player after `currentId` in seating circle order. */
export const nextActiveInCircle = (
  circleIds: string[],
  currentId: string,
  activeIds: string[]
): string | null => {
  if (!circleIds.length || !activeIds.length) return null
  const start = circleIds.indexOf(currentId)
  const order = start >= 0 ? circleIds : activeIds
  const from = start >= 0 ? start : -1
  for (let step = 1; step <= order.length; step++) {
    const id = order[(from + step + order.length * 2) % order.length]
    if (id && activeIds.includes(id)) return id
  }
  return null
}

/** Fill missing circle fields on older saved pots. */
export const normalizeTablePot = (pot: TablePot): TablePot => {
  const returnAtPlayerId = pot.returnAtPlayerId || pot.contributions[0]?.playerId || ''
  const circlePlayerIds = pot.circlePlayerIds?.length
    ? pot.circlePlayerIds
    : pot.contributions.map((part) => part.playerId)
  const passCursorPlayerId =
    pot.passCursorPlayerId ||
    nextActiveInCircle(circlePlayerIds, returnAtPlayerId, circlePlayerIds) ||
    returnAtPlayerId
  return {
    ...pot,
    circlePlayerIds,
    returnAtPlayerId,
    passCursorPlayerId,
    contributions: pot.contributions.map((item) => ({ ...item }))
  }
}

/** Place a fine: chips leave the player into the table pot (общак). */
export const placeTableFine = (
  players: Player[],
  pots: TablePot[],
  tableId: string,
  tablePlayerIds: string[],
  playerId: string,
  amount: number
): { players: Player[]; pots: TablePot[]; event: ScoreEvent } => {
  const chips = Math.max(0, Math.round(amount))
  if (chips <= 0) throw new Error('Fine amount must be positive.')

  const active = orderedActiveOnTable(players, tablePlayerIds)
  const player = active.find((item) => item.id === playerId)
  if (!player) throw new Error('Player not found among active at this table.')
  if (player.balance < chips) throw new Error('Not enough chips for fine.')

  const deltas: Record<string, number> = { [playerId]: -chips }
  const nextPlayers = applyDeltas(players, deltas)
  const circlePlayerIds = active.map((item) => item.id)
  const passCursorPlayerId =
    nextActiveInCircle(circlePlayerIds, playerId, circlePlayerIds) || playerId

  const existing = potForTable(pots, tableId)
  let nextPots: TablePot[]
  if (existing) {
    // Extra fine restacks pot and restarts the circle from the new offender.
    nextPots = pots.map((pot) =>
      pot.tableId === tableId
        ? {
            ...pot,
            amount: pot.amount + chips,
            contributions: [...pot.contributions, { playerId, amount: chips }],
            circlePlayerIds,
            returnAtPlayerId: playerId,
            passCursorPlayerId
          }
        : pot
    )
  } else {
    nextPots = [
      ...pots,
      {
        id: uid(),
        tableId,
        amount: chips,
        contributions: [{ playerId, amount: chips }],
        circlePlayerIds,
        createdAt: new Date().toISOString(),
        returnAtPlayerId: playerId,
        passCursorPlayerId
      }
    ]
  }

  return {
    players: nextPlayers,
    pots: nextPots,
    event: {
      id: uid(),
      at: new Date().toISOString(),
      mode: 'tournament',
      tableId,
      scorerId: playerId,
      ballId: 'fine',
      deltas,
      kind: 'fine_place',
      note: `штраф ${chips} → общак`,
      potAmount: chips
    }
  }
}

/** Next scorer takes the whole pot. */
export const claimTablePot = (
  players: Player[],
  pots: TablePot[],
  tableId: string,
  scorerId: string
): { players: Player[]; pots: TablePot[]; claimed: number; event: ScoreEvent | null } => {
  const pot = potForTable(pots, tableId)
  if (!pot || pot.amount <= 0) {
    return { players, pots, claimed: 0, event: null }
  }

  const scorer = players.find((player) => player.id === scorerId)
  if (!scorer || scorer.status !== 'active') {
    throw new Error('Scorer not found.')
  }

  const claimed = pot.amount
  const deltas: Record<string, number> = { [scorerId]: claimed }
  return {
    players: applyDeltas(players, deltas),
    pots: pots.filter((item) => item.tableId !== tableId),
    claimed,
    event: {
      id: uid(),
      at: new Date().toISOString(),
      mode: 'tournament',
      tableId,
      scorerId,
      ballId: 'pot_claim',
      deltas,
      kind: 'fine_claim',
      note: `общак +${claimed}`,
      potAmount: claimed,
      potSnapshot: clonePot(pot)
    }
  }
}

/** Full circle without a score — contributors get chips back. */
export const returnTablePot = (
  players: Player[],
  pots: TablePot[],
  tableId: string
): { players: Player[]; pots: TablePot[]; event: ScoreEvent | null } => {
  const pot = potForTable(pots, tableId)
  if (!pot || pot.amount <= 0) {
    return { players, pots, event: null }
  }

  const deltas: Record<string, number> = {}
  for (const part of pot.contributions) {
    deltas[part.playerId] = (deltas[part.playerId] || 0) + part.amount
  }

  return {
    players: applyDeltas(players, deltas),
    pots: pots.filter((item) => item.tableId !== tableId),
    event: {
      id: uid(),
      at: new Date().toISOString(),
      mode: 'tournament',
      tableId,
      scorerId: pot.contributions[0]?.playerId || '',
      ballId: 'pot_return',
      deltas,
      kind: 'fine_return',
      note: `общак ${pot.amount} возврат (круг)`,
      potAmount: pot.amount,
      potSnapshot: clonePot(pot)
    }
  }
}

/**
 * Mark a miss («мимо») for the current pass cursor.
 * When the cursor would return to returnAtPlayerId, auto-return the pot.
 */
export const passTablePotMiss = (
  players: Player[],
  pots: TablePot[],
  tableId: string,
  playerId: string
): {
  pots: TablePot[]
  players: Player[]
  event: ScoreEvent | null
  advancedTo: string | null
} => {
  const pot = potForTable(pots, tableId)
  if (!pot || pot.amount <= 0) {
    return { pots, players, event: null, advancedTo: null }
  }
  if (pot.passCursorPlayerId !== playerId) {
    throw new Error('Сейчас мимо может отметить другой игрок (ход круга).')
  }

  const activeIds = orderedActiveOnTable(players, pot.circlePlayerIds).map((item) => item.id)
  if (activeIds.length < 2) {
    const returned = returnTablePot(players, pots, tableId)
    return { pots: returned.pots, players: returned.players, event: returned.event, advancedTo: null }
  }

  const nextId = nextActiveInCircle(pot.circlePlayerIds, pot.passCursorPlayerId, activeIds)
  if (!nextId || nextId === pot.returnAtPlayerId) {
    const returned = returnTablePot(players, pots, tableId)
    return { pots: returned.pots, players: returned.players, event: returned.event, advancedTo: null }
  }

  return {
    pots: pots.map((item) =>
      item.tableId === tableId ? { ...item, passCursorPlayerId: nextId } : item
    ),
    players,
    event: null,
    advancedTo: nextId
  }
}
