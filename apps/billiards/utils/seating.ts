import type { Player, PlayerCategory, TableSeat } from '~/types/kolkhoz'

const uid = () =>
  typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `tbl_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`

const shuffle = <T>(items: T[]): T[] => {
  const arr = [...items]
  for (let i = arr.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    const tmp = arr[i]!
    arr[i] = arr[j]!
    arr[j] = tmp
  }
  return arr
}

/**
 * Balance categories across tables with 3–5 seats each when possible.
 * Prefer spreading strong (cat 1) players. Shuffle within categories so
 * each reseat (e.g. new round) produces a fresh mix.
 */
export const seatPlayers = (players: Player[], tableCount: number): TableSeat[] => {
  const active = players.filter((player) => player.status === 'active')
  const count = Math.max(1, Math.min(tableCount, active.length || 1))

  const tables: TableSeat[] = Array.from({ length: count }, (_, index) => ({
    id: uid(),
    label: `Стол ${index + 1}`,
    playerIds: []
  }))

  if (!active.length) return tables

  const byCategory: Record<PlayerCategory, Player[]> = { 1: [], 2: [], 3: [] }
  for (const player of active) {
    byCategory[player.category].push(player)
  }

  const ordered = [
    ...shuffle(byCategory[1]),
    ...shuffle(byCategory[2]),
    ...shuffle(byCategory[3])
  ]
  ordered.forEach((player, index) => {
    tables[index % tables.length]!.playerIds.push(player.id)
  })

  // Soft rebalance: move from oversized (>5) to undersized (<3) when possible
  let guard = 0
  while (guard < 50) {
    guard += 1
    const oversized = tables.find((table) => table.playerIds.length > 5)
    const undersized = tables.find((table) => table.playerIds.length < 3 && table !== oversized)
    if (!oversized || !undersized) break
    const moved = oversized.playerIds.pop()
    if (!moved) break
    undersized.playerIds.push(moved)
  }

  return tables
}

export const movePlayerToTable = (
  tables: TableSeat[],
  playerId: string,
  targetTableId: string
): TableSeat[] => {
  return tables.map((table) => {
    const without = table.playerIds.filter((id) => id !== playerId)
    if (table.id === targetTableId) {
      return { ...table, playerIds: [...without, playerId] }
    }
    return { ...table, playerIds: without }
  })
}
