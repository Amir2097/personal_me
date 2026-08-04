import { describe, expect, it } from 'vitest'
import { calcHouseCut, calcPrizePool, playerPaid, splitPrizes, sumMoney } from '../utils/bank'
import type { BuyInRecord } from '../types/kolkhoz'

const buyIn = (partial: Partial<BuyInRecord> & Pick<BuyInRecord, 'id' | 'playerId' | 'money' | 'chips'>): BuyInRecord => ({
  at: new Date().toISOString(),
  kind: 'entry',
  ...partial
})

describe('bank math', () => {
  it('sums contributions and prize pool at 80%', () => {
    const buyIns = [
      buyIn({ id: '1', playerId: 'a', money: 500, chips: 20 }),
      buyIn({ id: '2', playerId: 'b', money: 500, chips: 20 }),
      buyIn({ id: '3', playerId: 'a', money: 500, chips: 50, kind: 'addon' })
    ]
    expect(sumMoney(buyIns)).toBe(1500)
    expect(playerPaid(buyIns, 'a')).toBe(1000)
    expect(calcPrizePool(1500, 80)).toBe(1200)
    expect(calcHouseCut(1500, 80)).toBe(300)
  })

  it('splits prizes by place percent', () => {
    const parts = splitPrizes(1000, [
      { place: 1, percent: 50 },
      { place: 2, percent: 30 },
      { place: 3, percent: 20 }
    ])
    expect(parts.map((p) => p.amount)).toEqual([500, 300, 200])
  })
})
