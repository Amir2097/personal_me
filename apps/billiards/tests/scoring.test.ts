import { describe, expect, it } from 'vitest'
import {
  applyDropout,
  previousPlayerId,
  processCasualScore,
  processTournamentScore,
  totalBalance,
  undoEvent
} from '../utils/scoring'
import { seatPlayers } from '../utils/seating'
import type { Player, RoundConfig } from '../types/kolkhoz'

const player = (partial: Partial<Player> & Pick<Player, 'id' | 'name' | 'category'>): Player => ({
  handicap: 1,
  startingStack: 100,
  balance: 100,
  status: 'active',
  ...partial
})

describe('previous player', () => {
  it('picks the player before scorer in circle order', () => {
    expect(previousPlayerId(['a', 'b', 'c'], 'a')).toBe('c')
    expect(previousPlayerId(['a', 'b', 'c'], 'b')).toBe('a')
    expect(previousPlayerId(['a', 'b', 'c'], 'c')).toBe('b')
  })
})

describe('tournament scoring', () => {
  const round: RoundConfig = {
    number: 1,
    durationMinutes: 20,
    tariffs: { 1: 4, 2: 3, 3: 2 }
  }

  it('takes chips only from the previous player by THEIR category tariff', () => {
    const players = [
      player({ id: 'a', name: 'A', category: 1 }),
      player({ id: 'b', name: 'B', category: 3 }),
      player({ id: 'c', name: 'C', category: 1 })
    ]
    const before = totalBalance(players)
    // Order a→b→c; A scores vs previous C (cat1 → pays 4)
    const { players: next, event } = processTournamentScore(
      players,
      ['a', 'b', 'c'],
      'a',
      round,
      't1'
    )
    expect(event.deltas.a).toBe(4)
    expect(event.deltas.c).toBe(-4)
    expect(event.deltas.b).toBeUndefined()
    expect(next.find((p) => p.id === 'a')!.balance).toBe(104)
    expect(next.find((p) => p.id === 'b')!.balance).toBe(100)
    expect(totalBalance(next)).toBe(before)
  })

  it('undo restores balances', () => {
    const players = [
      player({ id: 'a', name: 'A', category: 1 }),
      player({ id: 'b', name: 'B', category: 2 })
    ]
    const { players: scored, event } = processTournamentScore(players, ['a', 'b'], 'a', round, 't1')
    const restored = undoEvent(scored, event)
    expect(restored.map((p) => p.balance)).toEqual([100, 100])
  })
})

describe('casual scoring', () => {
  it('charges only the previous player with ball × their handicap', () => {
    const players = [
      player({ id: 'a', name: 'A', category: 2, handicap: 1 }),
      player({ id: 'b', name: 'B', category: 2, handicap: 1.5 }),
      player({ id: 'c', name: 'C', category: 2, handicap: 1 })
    ]
    const ball = { id: 'yellow', label: 'Жёлтый', multiplier: 2, color: '#eab308' }
    // A scores vs previous C: 2 * 1 = 2
    const { event } = processCasualScore(players, ['a', 'b', 'c'], 'a', ball, 1, 'casual')
    expect(event.deltas.a).toBe(2)
    expect(event.deltas.c).toBe(-2)
    expect(event.deltas.b).toBeUndefined()
  })

  it('B scores vs previous A', () => {
    const players = [
      player({ id: 'a', name: 'A', category: 2, handicap: 1 }),
      player({ id: 'b', name: 'B', category: 2, handicap: 1 }),
      player({ id: 'c', name: 'C', category: 2, handicap: 1 })
    ]
    const ball = { id: 'standard', label: 'Обычный', multiplier: 1, color: '#fff' }
    const { event } = processCasualScore(players, ['a', 'b', 'c'], 'b', ball, 1, 'casual')
    expect(event.deltas.b).toBe(1)
    expect(event.deltas.a).toBe(-1)
    expect(event.deltas.c).toBeUndefined()
  })

  it('negative multiplier acts as penalty for scorer toward previous', () => {
    const players = [
      player({ id: 'a', name: 'A', category: 2 }),
      player({ id: 'b', name: 'B', category: 2 })
    ]
    const ball = { id: 'penalty', label: 'Штраф', multiplier: -2, color: '#a855f7' }
    const { event } = processCasualScore(players, ['a', 'b'], 'a', ball, 1, 'casual')
    // previous of A is B; A pays B 2
    expect(event.deltas.a).toBe(-2)
    expect(event.deltas.b).toBe(2)
    expect(event.kind).toBe('penalty')
  })
})

describe('dropout and seating', () => {
  it('marks player eliminated', () => {
    const players = [player({ id: 'a', name: 'A', category: 1 }), player({ id: 'b', name: 'B', category: 2 })]
    const { players: next } = applyDropout(players, 'a', 't1')
    expect(next.find((p) => p.id === 'a')!.status).toBe('eliminated')
  })

  it('spreads categories across tables', () => {
    const players = [
      player({ id: '1', name: '1', category: 1 }),
      player({ id: '2', name: '2', category: 1 }),
      player({ id: '3', name: '3', category: 2 }),
      player({ id: '4', name: '4', category: 2 }),
      player({ id: '5', name: '5', category: 3 }),
      player({ id: '6', name: '6', category: 3 })
    ]
    const tables = seatPlayers(players, 2)
    expect(tables).toHaveLength(2)
    expect(tables[0]!.playerIds.length + tables[1]!.playerIds.length).toBe(6)
  })
})
