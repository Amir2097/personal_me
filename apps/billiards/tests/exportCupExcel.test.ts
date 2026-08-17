import { describe, expect, it } from 'vitest'
import { buildCupWorkbook } from '../utils/exportCupExcel'
import { createEmptyCupState, cupUid } from '../types/cup'

describe('exportCupExcel', () => {
  it('builds summary, players and matches sheets', () => {
    const state = createEmptyCupState()
    state.tournament.name = 'Кубок тест'
    state.tournament.format = 'se'
    state.tournament.raceTo = 3
    state.players = [
      { id: 'p1', name: 'Анна', seed: 1 },
      { id: 'p2', name: 'Борис', seed: 2, username: 'boris' }
    ]
    state.matches = [
      {
        id: cupUid('m'),
        roundKey: 'final',
        roundLabel: 'Финал',
        bracketSide: 'final',
        order: 1,
        displayNo: 1,
        playerAId: 'p1',
        playerBId: 'p2',
        tableNo: 1,
        status: 'done',
        framesA: 3,
        framesB: 1,
        ballsA: 0,
        ballsB: 0,
        winnerId: 'p1',
        nextMatchId: null,
        nextSlot: null,
        loserNextMatchId: null,
        loserNextSlot: null
      }
    ]

    const wb = buildCupWorkbook(state)
    expect(wb.SheetNames).toEqual(['Сводка', 'Игроки', 'Матчи'])

    const playersSheet = wb.Sheets['Игроки']
    expect(playersSheet.A2.v).toBe(1)
    expect(playersSheet.B2.v).toBe('Анна')
    expect(playersSheet.C3.v).toBe('boris')

    const matchesSheet = wb.Sheets['Матчи']
    expect(matchesSheet.D2.v).toBe('Анна')
    expect(matchesSheet.F2.v).toBe('3:1')
  })
})
