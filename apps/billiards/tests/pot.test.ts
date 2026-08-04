import { describe, expect, it } from 'vitest'
import {
  claimTablePot,
  nextActiveInCircle,
  passTablePotMiss,
  placeTableFine,
  returnTablePot
} from '../utils/pot'
import type { Player } from '../types/kolkhoz'

const player = (partial: Partial<Player> & Pick<Player, 'id' | 'name' | 'category'>): Player => ({
  handicap: 1,
  startingStack: 100,
  balance: 100,
  status: 'active',
  ...partial
})

describe('table fine pot (общак)', () => {
  it('places fine chips into pot and starts circle after offender', () => {
    const players = [
      player({ id: 'a', name: 'A', category: 1 }),
      player({ id: 'b', name: 'B', category: 2 }),
      player({ id: 'c', name: 'C', category: 3 })
    ]
    const { players: next, pots, event } = placeTableFine(players, [], 't1', ['a', 'b', 'c'], 'b', 3)
    expect(event.kind).toBe('fine_place')
    expect(next.find((p) => p.id === 'b')!.balance).toBe(97)
    expect(pots[0]!.amount).toBe(3)
    expect(pots[0]!.returnAtPlayerId).toBe('b')
    expect(pots[0]!.passCursorPlayerId).toBe('c')
  })

  it('next claimer takes the whole pot', () => {
    const players = [
      player({ id: 'a', name: 'A', category: 1 }),
      player({ id: 'b', name: 'B', category: 2, balance: 97 })
    ]
    const placed = placeTableFine(players, [], 't1', ['a', 'b'], 'b', 3)
    const claimed = claimTablePot(placed.players, placed.pots, 't1', 'a')
    expect(claimed.claimed).toBe(3)
    expect(claimed.players.find((p) => p.id === 'a')!.balance).toBe(103)
    expect(claimed.pots).toHaveLength(0)
    expect(claimed.event?.kind).toBe('fine_claim')
  })

  it('returns pot to contributors when circle ends without score', () => {
    const players = [
      player({ id: 'a', name: 'A', category: 1 }),
      player({ id: 'b', name: 'B', category: 2 })
    ]
    const placed = placeTableFine(players, [], 't1', ['a', 'b'], 'b', 4)
    const returned = returnTablePot(placed.players, placed.pots, 't1')
    expect(returned.players.find((p) => p.id === 'b')!.balance).toBe(100)
    expect(returned.pots).toHaveLength(0)
    expect(returned.event?.kind).toBe('fine_return')
  })

  it('stacks multiple fines into one pot and restarts circle', () => {
    const players = [
      player({ id: 'a', name: 'A', category: 1 }),
      player({ id: 'b', name: 'B', category: 2 })
    ]
    const first = placeTableFine(players, [], 't1', ['a', 'b'], 'a', 2)
    const second = placeTableFine(first.players, first.pots, 't1', ['a', 'b'], 'b', 5)
    expect(second.pots[0]!.amount).toBe(7)
    expect(second.pots[0]!.contributions).toHaveLength(2)
    expect(second.pots[0]!.returnAtPlayerId).toBe('b')
    expect(second.pots[0]!.passCursorPlayerId).toBe('a')
  })

  it('auto-returns after full circle of misses', () => {
    const players = [
      player({ id: 'a', name: 'A', category: 1 }),
      player({ id: 'b', name: 'B', category: 2 }),
      player({ id: 'c', name: 'C', category: 3 })
    ]
    // A fines → cursor B
    const placed = placeTableFine(players, [], 't1', ['a', 'b', 'c'], 'a', 5)
    expect(placed.pots[0]!.passCursorPlayerId).toBe('b')

    const afterB = passTablePotMiss(placed.players, placed.pots, 't1', 'b')
    expect(afterB.event).toBeNull()
    expect(afterB.advancedTo).toBe('c')
    expect(afterB.pots[0]!.passCursorPlayerId).toBe('c')

    const afterC = passTablePotMiss(afterB.players, afterB.pots, 't1', 'c')
    expect(afterC.event?.kind).toBe('fine_return')
    expect(afterC.pots).toHaveLength(0)
    expect(afterC.players.find((p) => p.id === 'a')!.balance).toBe(100)
  })

  it('nextActiveInCircle wraps around', () => {
    expect(nextActiveInCircle(['a', 'b', 'c'], 'c', ['a', 'b', 'c'])).toBe('a')
    expect(nextActiveInCircle(['a', 'b', 'c'], 'a', ['a', 'b', 'c'])).toBe('b')
  })
})
