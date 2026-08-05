import { describe, expect, it } from 'vitest'
import { computeDebtTransfers } from '../utils/debts'
import type { Player } from '../types/kolkhoz'

const player = (partial: Partial<Player> & Pick<Player, 'id' | 'name' | 'balance'>): Player => ({
  category: 2,
  handicap: 0,
  startingStack: 0,
  status: 'active',
  ...partial
})

describe('debt transfers', () => {
  it('matches multiple creditors and debtors', () => {
    const transfers = computeDebtTransfers([
      player({ id: 'a', name: 'A', balance: 200 }),
      player({ id: 'b', name: 'B', balance: 100 }),
      player({ id: 'c', name: 'C', balance: -200 }),
      player({ id: 'd', name: 'D', balance: -100 })
    ])
    expect(transfers).toEqual([
      { fromId: 'c', toId: 'a', amount: 200 },
      { fromId: 'd', toId: 'b', amount: 100 }
    ])
  })
})
