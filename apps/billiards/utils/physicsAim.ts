import type { Exercise, Point2D } from '~/types/academy'

/**
 * Ideal cue aim point for demo animation.
 * Prefer ghost ball (cut geometry), else first white aiming trajectory tip, else first target.
 */
export const idealAimPoint = (exercise: Exercise): Point2D | null => {
  if (exercise.ghost_ball) {
    return { x: exercise.ghost_ball.x, y: exercise.ghost_ball.y }
  }

  const cue = exercise.balls.find((ball) => ball.type === 'cue')
  if (!cue) return null

  const aimTraj = exercise.trajectories.find(
    (traj) =>
      traj.color === '#ffffff' &&
      Math.hypot(traj.from.x - cue.x, traj.from.y - cue.y) < 0.6
  )
  if (aimTraj) {
    return { x: aimTraj.to.x, y: aimTraj.to.y }
  }

  const target = exercise.balls.find((ball) => ball.type === 'target')
  if (!target) return null
  return { x: target.x, y: target.y }
}

export const idealStrikeSpeed = (exercise: Exercise): number =>
  typeof exercise.physics_speed === 'number' && exercise.physics_speed > 0
    ? exercise.physics_speed
    : 56
