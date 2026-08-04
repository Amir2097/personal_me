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

export const tableLabel = (number: number) => `Стол №${number}`

/** Create/resize table slots so numbers can be set before seating. */
export const ensureTableSlots = (tableCount: number, existingTables: TableSeat[] = []): TableSeat[] => {
  const count = Math.max(1, Math.min(12, tableCount))
  return Array.from({ length: count }, (_, index) => {
    const prev = existingTables[index]
    const number = prev?.number && prev.number > 0 ? prev.number : index + 1
    return {
      id: prev?.id ?? uid(),
      number,
      label: tableLabel(number),
      playerIds: prev?.playerIds ? [...prev.playerIds] : []
    }
  })
}

/**
 * Жеребьёвка столов:
 * 1) Только активные игроки.
 * 2) Внутри каждой группы (1 → 2 → 3) список перемешивается случайно.
 * 3) Игроки раскладываются по кругу по уже заданным столам (номера сохраняются).
 * 4) Мягкая балансировка: со стола >5 мест перенос на стол <3.
 */
export const seatPlayers = (
  players: Player[],
  tableCount: number,
  existingTables: TableSeat[] = []
): TableSeat[] => {
  const active = players.filter((player) => player.status === 'active')
  // Keep the configured table count (and numbers), even if some tables stay empty.
  const tables = ensureTableSlots(tableCount, existingTables).map((table) => ({
    ...table,
    playerIds: [] as string[]
  }))

  if (!active.length || !tables.length) return tables

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
