import { describe, expect, it } from 'vitest'
import exercisesRaw from '../data/exercises.json'
import type { Exercise } from '../types/academy'
import {
  createSimState,
  DEMO_TABLE,
  directionBetween,
  simulateUntilIdle,
  stepSimulation,
  strikeCueBall
} from '../utils/billiardPhysics'
import { idealAimPoint, idealStrikeSpeed } from '../utils/physicsAim'

const exercises = exercisesRaw as Exercise[]
const BALL_RADIUS = 1.6

const byId = (id: string) => {
  const exercise = exercises.find((item) => item.id === id)
  if (!exercise) throw new Error(`Missing exercise ${id}`)
  return exercise
}

const runIdealShot = (exercise: Exercise, speed = idealStrikeSpeed(exercise)) => {
  const cue = exercise.balls.find((ball) => ball.type === 'cue')
  const aim = idealAimPoint(exercise)
  if (!cue || !aim) throw new Error(`No aim for ${exercise.id}`)

  let state = createSimState(
    exercise.balls.map((ball) => ({
      id: ball.id,
      type: ball.type,
      label: ball.label,
      x: ball.x,
      y: ball.y
    })),
    DEMO_TABLE
  )
  strikeCueBall(state, cue.id, directionBetween(cue, aim), speed)
  return simulateUntilIdle(state, { config: DEMO_TABLE })
}

describe('physicsAim batch-1 ideal shots', () => {
  const batch = [
    'ex_01_direct_target',
    'ex_02_cut_shot_3_4',
    'ex_03_stop_shot',
    'ex_16_follow_shot',
    'ex_17_short_rail_pot',
    'ex_18_thin_cut_corner'
  ]

  for (const id of batch) {
    it(`${id} has physics_demo and pockets a target`, () => {
      const exercise = byId(id)
      expect(exercise.physics_demo).toBe(true)
      const state = runIdealShot(exercise)
      const pocketed = state.balls.some((ball) => ball.type === 'target' && !ball.active)
      expect(pocketed).toBe(true)
    })
  }

  it('ex_03_stop_shot leaves cue near contact zone', () => {
    const state = runIdealShot(byId('ex_03_stop_shot'))
    const cue = state.balls.find((ball) => ball.type === 'cue')
    expect(cue?.active).toBe(true)
    expect(Math.hypot(cue!.x - 50, cue!.y - 18)).toBeLessThan(4)
  })

  it('idealAimPoint prefers ghost ball when present', () => {
    const exercise = byId('ex_02_cut_shot_3_4')
    const aim = idealAimPoint(exercise)
    expect(aim).toEqual({ x: exercise.ghost_ball!.x, y: exercise.ghost_ball!.y })
  })

  it('ex_17 matches short-rail instructions and pots cleanly', () => {
    const exercise = byId('ex_17_short_rail_pot')
    const cue = exercise.balls.find((ball) => ball.type === 'cue')!
    const target = exercise.balls.find((ball) => ball.type === 'target')!

    // Target ~3–5 cm from short rail (table length 100 ≈ 355 cm → ~1.13 units ≈ 4 cm).
    const gapUnits = 100 - (target.x + BALL_RADIUS)
    expect(gapUnits).toBeGreaterThan(0.85)
    expect(gapUnits).toBeLessThan(1.55)

    // Cue sits slightly farther from the short rail than the object ball.
    expect(cue.x).toBeLessThan(target.x)

    // Aim line is nearly parallel to the short rail (mostly along Y).
    const aim = idealAimPoint(exercise)!
    const dir = directionBetween(cue, aim)
    expect(Math.abs(dir.y)).toBeGreaterThan(Math.abs(dir.x) * 3)

    expect(exercise.annotations?.[0]?.label).toBe('3–5 см')

    // Object-ball path aims into the pocket mouth (not along the short cushion into the jaw tip).
    const pocketAim = exercise.trajectories.find((traj) => traj.color === '#facc15')!.to
    const railTouchX = 100 - BALL_RADIUS
    const dx = pocketAim.x - target.x
    const dy = pocketAim.y - target.y
    const tRail = (railTouchX - target.x) / dx
    const yAtRail = target.y + dy * tRail
    const distAtRail = Math.hypot(100 - railTouchX, 0 - yAtRail)
    expect(pocketAim.x).toBeLessThan(99.5)
    expect(distAtRail).toBeLessThan(DEMO_TABLE.pocketRadius + BALL_RADIUS * 3.4)

    let state = createSimState(
      exercise.balls.map((ball) => ({
        id: ball.id,
        type: ball.type,
        label: ball.label,
        x: ball.x,
        y: ball.y
      })),
      DEMO_TABLE
    )
    strikeCueBall(state, cue.id, directionBetween(cue, aim), idealStrikeSpeed(exercise))

    let sawRailBounce = false
    let hitStarted = false
    let peakX = target.x
    for (let i = 0; i < 8000; i += 1) {
      state = stepSimulation(state, 1 / 120, DEMO_TABLE)
      const moving = state.balls.find((ball) => ball.id === 'target_1')!
      if (!moving.active) break
      if (Math.hypot(moving.vx, moving.vy) > 1) hitStarted = true
      if (!hitStarted) continue
      peakX = Math.max(peakX, moving.x)
      // A cushion bounce near the short rail throws the ball back inward before the jaws.
      if (moving.y > 7 && moving.x < peakX - 0.9) sawRailBounce = true
    }

    const pocketed = state.balls.find((ball) => ball.id === 'target_1')!
    expect(pocketed.active).toBe(false)
    expect(pocketed.x).toBe(100)
    expect(pocketed.y).toBe(0)
    expect(sawRailBounce).toBe(false)
  })
})
