import { describe, expect, it } from 'vitest'
import { applyCasualFoul, playerStakePrice } from '../utils/casualPenalties'
import { createCasualParty, potCasualBall } from '../utils/casual'
import type { Player, SpecialBall } from '../types/kolkhoz'

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

const tableIds = ['a', 'b', 'c', 'd']

describe('casual penalties', () => {
  it('pay_all charges offender per opponent at table price', () => {
    const party = createCasualParty(1)
    const players = [
      player({ id: 'a', name: 'A' }),
      player({ id: 'b', name: 'B' }),
      player({ id: 'c', name: 'C' }),
      player({ id: 'd', name: 'D' })
    ]

    const result = applyCasualFoul(party, players, tableIds, 'a', { mode: 'pay_all', usePersonalStake: false }, 100, 't1')

    expect(result.amountEach).toBe(100)
    expect(result.players.find((p) => p.id === 'a')?.balance).toBe(-300)
    expect(result.players.find((p) => p.id === 'b')?.balance).toBe(100)
    expect(result.event.kind).toBe('casual_foul')
  })

  it('pay_all with personal stake uses offender stake price', () => {
    const party = createCasualParty(1)
    const players = [
      player({ id: 'a', name: 'A', stakePrice: 150 }),
      player({ id: 'b', name: 'B' }),
      player({ id: 'c', name: 'C' })
    ]

    const result = applyCasualFoul(
      party,
      players,
      ['a', 'b', 'c'],
      'a',
      { mode: 'pay_all', usePersonalStake: true },
      100,
      't1'
    )

    expect(result.amountEach).toBe(150)
    expect(result.players.find((p) => p.id === 'a')?.balance).toBe(-300)
    expect(playerStakePrice(players[0], 100)).toBe(150)
  })

  it('ball_from_home removes potted ball and adds to table', () => {
    let party = createCasualParty(1)
    party = potCasualBall(party, standardBall, 100, ['a', 'b'], 'a', 't1', 'B').party
    party = potCasualBall(party, standardBall, 100, ['a', 'b'], 'a', 't1', 'B').party

    const players = [player({ id: 'a', name: 'A' }), player({ id: 'b', name: 'B' })]
    const result = applyCasualFoul(
      party,
      players,
      ['a', 'b'],
      'a',
      { mode: 'ball_from_home', usePersonalStake: true },
      100,
      't1'
    )

    expect(result.party.ballsOnTable).toBe(1)
    expect(result.party.rackPointsByPlayer.a).toBe(1)
    expect(result.event.note).toContain('выставлен')
  })

  it('ball_from_home with no potted balls creates debt', () => {
    const party = createCasualParty(1)
    const players = [player({ id: 'a', name: 'A' }), player({ id: 'b', name: 'B' })]

    const result = applyCasualFoul(
      party,
      players,
      ['a', 'b'],
      'a',
      { mode: 'ball_from_home', usePersonalStake: true },
      100,
      't1'
    )

    expect(result.party.ballDebtByPlayer?.a).toBe(1)
    expect(result.event.note).toContain('долг')
  })

  it('first pot after debt puts ball on table', () => {
    let party = createCasualParty(1)
    party = applyCasualFoul(
      party,
      [player({ id: 'a', name: 'A' }), player({ id: 'b', name: 'B' })],
      ['a', 'b'],
      'a',
      { mode: 'ball_from_home', usePersonalStake: true },
      100,
      't1'
    ).party

    const pot = potCasualBall(party, standardBall, 100, ['a', 'b'], 'a', 't1', 'B')
    expect(pot.party.ballDebtByPlayer?.a).toBeUndefined()
    expect(pot.party.ballsOnTable).toBe(1)
  })

  it('pass_advantage grants free shot to next player', () => {
    const party = createCasualParty(1)
    const players = [player({ id: 'a', name: 'A' }), player({ id: 'b', name: 'B' }), player({ id: 'c', name: 'C' })]

    const result = applyCasualFoul(
      party,
      players,
      ['a', 'b', 'c'],
      'a',
      { mode: 'pass_advantage', usePersonalStake: true },
      100,
      't1'
    )

    expect(result.party.freeShotForPlayerId).toBe('b')
    expect(result.event.note).toContain('B')
  })
})
