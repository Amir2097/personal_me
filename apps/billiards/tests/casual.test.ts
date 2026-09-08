import { describe, expect, it } from 'vitest'
import {
  ballPointsForIndex,
  calcPartySettlement,
  createCasualParty,
  effectivePartyScore,
  extraPointsForPot,
  isRackComplete,
  partyTargetNorm,
  potCasualBall,
  rackPointsForPot,
  rotatePlayerOrder,
  settleCasualParty
} from '../utils/casual'
import { computeDebtTransfers } from '../utils/debts'
import {
  canRemoveCasualBall,
  DEFAULT_CASUAL_BALLS,
  type Player,
  type SpecialBall
} from '../types/kolkhoz'

const player = (partial: Partial<Player> & Pick<Player, 'id' | 'name'>): Player => ({
  category: 2,
  handicap: 0,
  startingStack: 0,
  balance: 0,
  status: 'active',
  ...partial
})

const standardBall: SpecialBall = {
  id: 'standard',
  label: 'Обычный',
  price: 100,
  color: '#fff',
  partyRole: 'rack'
}

const yellowBall: SpecialBall = {
  id: 'yellow',
  label: 'Жёлтый',
  price: 200,
  color: '#eab308',
  partyRole: 'rack'
}

const bonusBall: SpecialBall = {
  id: 'bonus',
  label: 'Бонус',
  price: 100,
  color: '#22c55e',
  partyRole: 'extra'
}

describe('casual party points', () => {
  it('last ball counts double', () => {
    expect(ballPointsForIndex(1)).toBe(1)
    expect(ballPointsForIndex(14)).toBe(1)
    expect(ballPointsForIndex(15)).toBe(2)
  })

  it('detects full rack at 16 points', () => {
    const party = createCasualParty(1)
    party.rackPointsByPlayer = { a: 6, b: 5, c: 3, d: 2 }
    party.rackPointsTotal = 16
    expect(isRackComplete(party)).toBe(true)
  })
})

describe('casual settlement — 4 players example', () => {
  it('matches norm 4 and ruble balances at 100 ₽/point', () => {
    const party = createCasualParty(1)
    party.rackPointsByPlayer = { a: 6, b: 5, c: 3, d: 2 }
    party.rackPointsTotal = 16
    const players = [
      player({ id: 'a', name: 'A' }),
      player({ id: 'b', name: 'B' }),
      player({ id: 'c', name: 'C' }),
      player({ id: 'd', name: 'D' })
    ]
    const lines = calcPartySettlement(party, players, ['a', 'b', 'c', 'd'], 100)
    expect(partyTargetNorm(4)).toBe(4)
    expect(lines[0]?.method).toBe('norm')
    expect(lines.find((line) => line.playerId === 'a')?.deltaMoney).toBe(200)
    expect(lines.find((line) => line.playerId === 'b')?.deltaMoney).toBe(100)
    expect(lines.find((line) => line.playerId === 'c')?.deltaMoney).toBe(-100)
    expect(lines.find((line) => line.playerId === 'd')?.deltaMoney).toBe(-200)
  })
})

describe('casual settlement — 3 players without handicap', () => {
  it('uses pairwise comparison', () => {
    const party = createCasualParty(1)
    party.rackPointsByPlayer = { a: 8, b: 5, c: 3 }
    party.rackPointsTotal = 16
    const players = [
      player({ id: 'a', name: 'A' }),
      player({ id: 'b', name: 'B' }),
      player({ id: 'c', name: 'C' })
    ]
    const lines = calcPartySettlement(party, players, ['a', 'b', 'c'], 100)
    expect(lines[0]?.method).toBe('pairwise')
    expect(lines.find((line) => line.playerId === 'a')?.deltaMoney).toBe(800)
    expect(lines.find((line) => line.playerId === 'b')?.deltaMoney).toBe(-100)
    expect(lines.find((line) => line.playerId === 'c')?.deltaMoney).toBe(-700)
  })
})

describe('casual settlement — handicap +2 for beginner', () => {
  it('matches the 3-player example with fora', () => {
    const party = createCasualParty(1)
    party.rackPointsByPlayer = { a: 7, b: 6, v: 3 }
    party.rackPointsTotal = 16
    const players = [
      player({ id: 'a', name: 'A' }),
      player({ id: 'b', name: 'B' }),
      player({ id: 'v', name: 'V', handicap: 2 })
    ]
    expect(effectivePartyScore(party, players[2]!)).toBe(5)
    const lines = calcPartySettlement(party, players, ['a', 'b', 'v'], 100)
    expect(lines.find((line) => line.playerId === 'a')?.deltaMoney).toBe(300)
    expect(lines.find((line) => line.playerId === 'b')?.deltaMoney).toBe(0)
    expect(lines.find((line) => line.playerId === 'v')?.deltaMoney).toBe(-300)
  })
})

describe('ball party roles', () => {
  it('rack ball advances pyramid index and rack total', () => {
    const party = createCasualParty(1)
    const result = potCasualBall(party, standardBall, 100, ['a', 'b'], 'a', 't1', 'B')
    expect(result.party.ballIndex).toBe(1)
    expect(result.party.rackPointsTotal).toBe(1)
    expect(result.party.rackPointsByPlayer.a).toBe(1)
  })

  it('extra ball does not advance pyramid', () => {
    const party = createCasualParty(1)
    party.ballIndex = 5
    party.rackPointsTotal = 5
    const result = potCasualBall(party, bonusBall, 100, ['a', 'b'], 'a', 't1', 'B')
    expect(result.party.ballIndex).toBe(5)
    expect(result.party.rackPointsTotal).toBe(5)
    expect(result.party.extraPointsByPlayer.a).toBe(1)
  })

  it('rack yellow weighs double toward rack tally', () => {
    expect(rackPointsForPot(1, yellowBall, 100)).toBe(2)
    expect(extraPointsForPot(bonusBall, 100)).toBe(1)
  })
})

describe('session debts', () => {
  it('builds minimal transfer list', () => {
    const transfers = computeDebtTransfers([
      player({ id: 'a', name: 'A', balance: 300 }),
      player({ id: 'b', name: 'B', balance: 0 }),
      player({ id: 'v', name: 'V', balance: -300 })
    ])
    expect(transfers).toEqual([{ fromId: 'v', toId: 'a', amount: 300 }])
  })
})

describe('casual rotation', () => {
  it('moves first player to the end', () => {
    const players = [
      player({ id: 'a', name: 'A' }),
      player({ id: 'b', name: 'B' }),
      player({ id: 'c', name: 'C' })
    ]
    const rotated = rotatePlayerOrder(players)
    expect(rotated.map((item) => item.id)).toEqual(['b', 'c', 'a'])
  })
})

describe('pot and settle flow', () => {
  it('records balls and applies settlement to balances', () => {
    let party = createCasualParty(1)
    const players = [
      player({ id: 'a', name: 'A' }),
      player({ id: 'b', name: 'B' }),
      player({ id: 'c', name: 'C' }),
      player({ id: 'd', name: 'D' })
    ]
    const order = ['a', 'b', 'c', 'd']

    const r1 = potCasualBall(party, standardBall, 100, order, 'a', 't1', 'D')
    party = r1.party
    expect(party.rackPointsByPlayer.a).toBe(1)

    party.rackPointsByPlayer = { a: 6, b: 5, c: 3, d: 2 }
    party.rackPointsTotal = 16
    party.ballIndex = 15

    const settled = settleCasualParty(party, players, order, 100, 't1')
    expect(settled.players.find((item) => item.id === 'a')!.balance).toBe(200)
    expect(settled.players.find((item) => item.id === 'd')!.balance).toBe(-200)
    expect(settled.players.map((item) => item.id)).toEqual(['b', 'c', 'd', 'a'])
    expect(settled.party.number).toBe(2)
  })
})

describe('canRemoveCasualBall', () => {
  const balls = () => DEFAULT_CASUAL_BALLS.map((ball) => ({ ...ball }))

  it('allows removing yellow/red/black before play', () => {
    expect(canRemoveCasualBall(balls(), 'yellow')).toBe(true)
    expect(canRemoveCasualBall(balls(), 'red')).toBe(true)
    expect(canRemoveCasualBall(balls(), 'black')).toBe(true)
  })

  it('never allows removing the standard ball', () => {
    expect(canRemoveCasualBall(balls(), 'standard')).toBe(false)
  })

  it('blocks removal while party has activity', () => {
    expect(canRemoveCasualBall(balls(), 'yellow', { partyHasActivity: true })).toBe(false)
  })

  it('blocks removing the last rack ball', () => {
    const onlyStandard: SpecialBall[] = [
      { id: 'standard', label: 'Обычный', price: 100, color: '#fff', partyRole: 'rack' },
      { id: 'custom', label: 'Доп', price: 50, color: '#888', partyRole: 'extra' }
    ]
    expect(canRemoveCasualBall(onlyStandard, 'standard')).toBe(false)
    expect(canRemoveCasualBall(onlyStandard, 'custom')).toBe(true)
  })
})
