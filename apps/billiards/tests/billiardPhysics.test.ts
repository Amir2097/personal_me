import { describe, expect, it } from 'vitest'
import {
  createSimState,
  directionBetween,
  isSimulationIdle,
  simulateUntilIdle,
  strikeCueBall
} from '../utils/billiardPhysics'

describe('billiardPhysics', () => {
  it('transfers momentum on cue-target collision', () => {
    let state = createSimState([
      { id: 'cue', type: 'cue', label: 'Б', x: 70, y: 36 },
      { id: 'target_1', type: 'target', label: '1', x: 85, y: 18 }
    ])

    strikeCueBall(state, 'cue', directionBetween({ x: 70, y: 36 }, { x: 85, y: 18 }), 44)
    state = simulateUntilIdle(state)

    const cue = state.balls.find((ball) => ball.id === 'cue')
    const target = state.balls.find((ball) => ball.id === 'target_1')

    expect(isSimulationIdle(state)).toBe(true)
    expect(cue?.active).toBe(true)
    expect(target?.active).toBe(false)
  })

  it('slows balls with rolling friction until stop', () => {
    let state = createSimState([{ id: 'cue', type: 'cue', label: 'Б', x: 25, y: 25 }])
    strikeCueBall(state, 'cue', { x: 1, y: 0 }, 30)
    state = simulateUntilIdle(state)

    const cue = state.balls.find((ball) => ball.id === 'cue')
    expect(cue?.vx).toBe(0)
    expect(cue?.vy).toBe(0)
    expect(cue!.x).toBeGreaterThan(25)
  })

  it('bounces off cushions', () => {
    let state = createSimState([{ id: 'cue', type: 'cue', label: 'Б', x: 30, y: 25 }])
    strikeCueBall(state, 'cue', { x: 1, y: 0.15 }, 32)
    state = simulateUntilIdle(state)

    const cue = state.balls.find((ball) => ball.id === 'cue')
    expect(cue?.active).toBe(true)
    expect(cue!.x).toBeGreaterThan(30)
    expect(cue!.y).toBeGreaterThan(0)
    expect(cue!.y).toBeLessThan(50)
  })
})
