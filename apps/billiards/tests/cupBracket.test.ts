import { describe, expect, it } from 'vitest'
import { nextPowerOfTwo } from '../types/cup'
import { addBall, awardFrame } from '../utils/cupAdvance'
import {
  advanceWinner,
  buildBracket,
  buildDoubleElimination,
  buildSingleElimination,
  seedingOrder
} from '../utils/cupBracket'
import { buildBracketLayout } from '../utils/cupBracketLayout'
import { uniqueCupName } from '../utils/cupNames'
import type { CupPlayer } from '../types/cup'

const players = (...names: string[]): CupPlayer[] =>
  names.map((name, index) => ({ id: `p${index + 1}`, name, seed: index + 1 }))

describe('cupBracket SE', () => {
  it('pads to next power of two', () => {
    expect(nextPowerOfTwo(3)).toBe(4)
    expect(nextPowerOfTwo(5)).toBe(8)
    expect(seedingOrder(4)).toEqual([1, 4, 2, 3])
  })

  it('builds 4-player SE with final', () => {
    const { matches } = buildSingleElimination(players('A', 'B', 'C', 'D'))
    expect(matches.filter((match) => match.status === 'ready').length).toBe(2)
    expect(matches.some((match) => match.bracketSide === 'final')).toBe(true)
  })

  it('auto-completes BYE for 3 players', () => {
    const { matches } = buildSingleElimination(players('A', 'B', 'C'))
    const bye = matches.filter((match) => match.status === 'done' && match.roundKey.includes('r4'))
    expect(bye.length).toBeGreaterThanOrEqual(1)
    const semisReady = matches.filter((match) => match.roundKey.includes('r4') || match.roundLabel === '1/2')
    expect(semisReady.length).toBeGreaterThan(0)
  })

  it('advances winner through SE to tournament champion', () => {
    let { matches } = buildBracket('se', players('A', 'B', 'C', 'D'))
    const r1 = matches.filter((match) => match.status === 'ready')
    expect(r1.length).toBe(2)

    let result = advanceWinner(matches, r1[0].id, r1[0].playerAId!, 'se')
    matches = result.matches
    result = advanceWinner(matches, r1[1].id, r1[1].playerAId!, 'se')
    matches = result.matches

    const final = matches.find((match) => match.bracketSide === 'final')!
    expect(final.playerAId).toBeTruthy()
    expect(final.playerBId).toBeTruthy()
    expect(final.status).toBe('ready')

    result = advanceWinner(matches, final.id, final.playerAId!, 'se')
    expect(result.completed).toBe(true)
    expect(result.tournamentWinnerId).toBe(final.playerAId)
  })
})

describe('cupBracket DE', () => {
  it('builds 4-player DE on 4 slots without quarter-final byes', () => {
    const { matches } = buildDoubleElimination(players('A', 'B', 'C', 'D'))
    expect(matches.some((match) => match.bracketSide === 'losers')).toBe(true)
    expect(matches.some((match) => match.roundKey === 'de-final')).toBe(true)
    expect(matches.some((match) => match.roundLabel === 'Финал')).toBe(true)
    expect(matches.some((match) => match.roundLabel === 'Большой финал')).toBe(false)
    expect(matches.some((match) => match.roundLabel === '1/4')).toBe(false)
    expect(matches.filter((match) => match.roundKey === 'se-r4').length).toBe(2)
    expect(matches.filter((match) => match.roundKey === 'se-r8').length).toBe(0)
    expect(matches.filter((match) => match.status === 'ready' && match.bracketSide === 'winners').length).toBe(2)
  })

  it('builds 8-player DE like bill4you: 2 upper tours, lower return, semis, final', () => {
    const { matches } = buildDoubleElimination(
      players('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')
    )
    expect(matches.filter((match) => match.roundKey === 'se-r8').length).toBe(4)
    expect(matches.filter((match) => match.roundKey === 'wb2-8').length).toBe(2)
    expect(matches.filter((match) => match.roundKey === 'wb-semi').length).toBe(2)
    expect(matches.filter((match) => match.roundKey === 'de-final').length).toBe(1)
    expect(matches.filter((match) => match.bracketSide === 'losers').length).toBe(4)
    expect(matches.length).toBe(13)
  })

  it('sends loser to losers bracket', () => {
    let { matches } = buildDoubleElimination(players('A', 'B', 'C', 'D'))
    const first = matches.find(
      (match) =>
        match.status === 'ready' &&
        match.bracketSide === 'winners' &&
        match.playerAId &&
        match.playerBId &&
        match.loserNextMatchId
    )!
    const result = advanceWinner(matches, first.id, first.playerAId!, 'de')
    matches = result.matches
    const lb = matches.find((match) => match.id === first.loserNextMatchId)!
    const loserId = first.playerBId
    expect(lb.playerAId === loserId || lb.playerBId === loserId).toBe(true)
  })

  it('builds 32-player DE with losers bracket', () => {
    const names = Array.from({ length: 32 }, (_, index) => `P${index + 1}`)
    const { matches } = buildDoubleElimination(players(...names))
    expect(matches.filter((match) => match.bracketSide === 'losers').length).toBeGreaterThan(8)
    expect(matches.some((match) => match.roundKey === 'de-final')).toBe(true)
    expect(matches.every((match) => match.displayNo > 0)).toBe(true)
  })

  it('lays out DE final as last upper column to the right', () => {
    const { matches } = buildDoubleElimination(players('A', 'B', 'C', 'D'))
    const layout = buildBracketLayout(matches, 'de')
    const final = layout.nodes.find((node) => node.match.roundKey === 'de-final')!
    const r2 = layout.nodes.find((node) => node.match.roundKey.startsWith('wb2-'))!
    expect(final.x).toBeGreaterThan(r2.x)
    expect(final.band).toBe('upper')
    expect(layout.lowerBandY).not.toBeNull()
  })

  it('does not overlap cards in the same column', () => {
    const { matches } = buildDoubleElimination(players('A', 'B', 'C', 'D'))
    const layout = buildBracketLayout(matches, 'de')
    const byX = new Map<number, number[]>()
    for (const node of layout.nodes) {
      const ys = byX.get(node.x) || []
      ys.push(node.y)
      byX.set(node.x, ys)
    }
    for (const ys of byX.values()) {
      ys.sort((a, b) => a - b)
      for (let i = 1; i < ys.length; i += 1) {
        expect(ys[i] - ys[i - 1]).toBeGreaterThanOrEqual(120)
      }
    }
  })
})

describe('cupAdvance scoring', () => {
  it('tracks balls and awards frames up to raceTo', () => {
    let match = buildSingleElimination(players('A', 'B')).matches.find((item) => item.status === 'ready')!
    match = addBall(match, 'A')
    match = addBall(match, 'A')
    expect(match.ballsA).toBe(2)

    let awarded = awardFrame(match, 'A', 2)
    expect(awarded.match.framesA).toBe(1)
    expect(awarded.match.ballsA).toBe(0)
    expect(awarded.raceWon).toBe(false)

    awarded = awardFrame(awarded.match, 'A', 2)
    expect(awarded.raceWon).toBe(true)
    expect(awarded.winnerId).toBe(match.playerAId)
  })
})

describe('uniqueCupName', () => {
  it('keeps the first title and suffixes duplicates', () => {
    expect(uniqueCupName('Кубок клуба', [])).toBe('Кубок клуба')
    expect(uniqueCupName('Кубок клуба', ['Кубок клуба'])).toBe('Кубок клуба 2')
    expect(uniqueCupName('Кубок клуба', ['Кубок клуба', 'Кубок клуба 2'])).toBe('Кубок клуба 3')
  })
})
