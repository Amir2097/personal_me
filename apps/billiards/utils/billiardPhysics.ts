import type { BallKind, Point2D } from '~/types/academy'

export type PhysBall = {
  id: string
  type: BallKind
  label: string
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  active: boolean
  pocketedAt?: number
}

export type TableConfig = {
  width: number
  height: number
  ballRadius: number
  pocketRadius: number
  pockets: Point2D[]
  /** Cushion bounce factor (0..1). */
  restitution: number
  /** Linear deceleration in table units / second². */
  rollingFriction: number
  /** Speed below which a ball is considered stopped. */
  stopSpeed: number
}

export const DEFAULT_TABLE: TableConfig = {
  width: 100,
  height: 50,
  ballRadius: 1.6,
  pocketRadius: 2.3,
  pockets: [
    { x: 0, y: 0 },
    { x: 50, y: 0 },
    { x: 100, y: 0 },
    { x: 0, y: 50 },
    { x: 50, y: 50 },
    { x: 100, y: 50 }
  ],
  restitution: 0.88,
  rollingFriction: 18,
  stopSpeed: 0.35
}

/** Softer cloth + larger mouths — for academy demo animations. */
export const DEMO_TABLE: TableConfig = {
  ...DEFAULT_TABLE,
  pocketRadius: 3.1,
  restitution: 0.92,
  rollingFriction: 11,
  stopSpeed: 0.25
}

export type SimState = {
  balls: PhysBall[]
  time: number
}

export type BallSeed = {
  id: string
  type: BallKind
  label: string
  x: number
  y: number
}

export const createSimState = (seeds: BallSeed[], config: TableConfig = DEFAULT_TABLE): SimState => ({
  time: 0,
  balls: seeds.map((seed) => ({
    id: seed.id,
    type: seed.type,
    label: seed.label,
    x: seed.x,
    y: seed.y,
    vx: 0,
    vy: 0,
    radius: config.ballRadius,
    active: true
  }))
})

const hypot = (x: number, y: number) => Math.hypot(x, y)

const normalize = (x: number, y: number) => {
  const len = hypot(x, y)
  if (len < 1e-8) return { x: 0, y: 0, len: 0 }
  return { x: x / len, y: y / len, len }
}

const applyRollingFriction = (ball: PhysBall, dt: number, friction: number, stopSpeed: number) => {
  const speed = hypot(ball.vx, ball.vy)
  if (speed <= stopSpeed) {
    ball.vx = 0
    ball.vy = 0
    return
  }
  const drop = friction * dt
  const next = Math.max(0, speed - drop)
  const scale = next / speed
  ball.vx *= scale
  ball.vy *= scale
  if (hypot(ball.vx, ball.vy) <= stopSpeed) {
    ball.vx = 0
    ball.vy = 0
  }
}

const pocketBall = (ball: PhysBall, pocket: Point2D, time: number) => {
  ball.active = false
  ball.vx = 0
  ball.vy = 0
  ball.x = pocket.x
  ball.y = pocket.y
  ball.pocketedAt = time
}

const nearestPocket = (ball: PhysBall, config: TableConfig) => {
  let best = config.pockets[0]
  let bestDist = Infinity
  for (const pocket of config.pockets) {
    const dist = hypot(ball.x - pocket.x, ball.y - pocket.y)
    if (dist < bestDist) {
      bestDist = dist
      best = pocket
    }
  }
  return { pocket: best, dist: bestDist }
}

const tryPocket = (ball: PhysBall, config: TableConfig, time: number) => {
  const catchRadius = config.pocketRadius + ball.radius * 0.85
  for (const pocket of config.pockets) {
    const dist = hypot(ball.x - pocket.x, ball.y - pocket.y)
    if (dist <= catchRadius) {
      pocketBall(ball, pocket, time)
      return true
    }
  }
  return false
}

const nearPocketMouth = (ball: PhysBall, config: TableConfig) => {
  // Wide jaws so near-rail corner shots fall in instead of scraping the cushion.
  const mouth = config.pocketRadius + ball.radius * 3.4
  return config.pockets.some((pocket) => hypot(ball.x - pocket.x, ball.y - pocket.y) <= mouth)
}

const resolveWall = (ball: PhysBall, config: TableConfig, time: number) => {
  // Near jaws: never bounce off the cushion — either fall in or keep rolling into the pocket.
  if (nearPocketMouth(ball, config)) {
    const outside =
      ball.x < 0 ||
      ball.x > config.width ||
      ball.y < 0 ||
      ball.y > config.height
    if (outside) {
      const { pocket } = nearestPocket(ball, config)
      pocketBall(ball, pocket, time)
    }
    return
  }

  const { width, height, restitution } = config
  const r = ball.radius

  if (ball.x - r < 0) {
    ball.x = r
    ball.vx = Math.abs(ball.vx) * restitution
  } else if (ball.x + r > width) {
    ball.x = width - r
    ball.vx = -Math.abs(ball.vx) * restitution
  }

  if (ball.y - r < 0) {
    ball.y = r
    ball.vy = Math.abs(ball.vy) * restitution
  } else if (ball.y + r > height) {
    ball.y = height - r
    ball.vy = -Math.abs(ball.vy) * restitution
  }
}

const resolveBallPair = (a: PhysBall, b: PhysBall) => {
  if (!a.active || !b.active) return

  const dx = b.x - a.x
  const dy = b.y - a.y
  const dist = hypot(dx, dy)
  const minDist = a.radius + b.radius
  if (dist >= minDist || dist < 1e-8) return

  const nx = dx / dist
  const ny = dy / dist
  const overlap = minDist - dist

  a.x -= nx * overlap * 0.5
  a.y -= ny * overlap * 0.5
  b.x += nx * overlap * 0.5
  b.y += ny * overlap * 0.5

  const relVx = a.vx - b.vx
  const relVy = a.vy - b.vy
  const relNormal = relVx * nx + relVy * ny
  if (relNormal <= 0) return

  a.vx -= relNormal * nx
  a.vy -= relNormal * ny
  b.vx += relNormal * nx
  b.vy += relNormal * ny
}

export const strikeCueBall = (
  state: SimState,
  cueId: string,
  direction: Point2D,
  speed: number
) => {
  const cue = state.balls.find((ball) => ball.id === cueId && ball.active)
  if (!cue) return false
  const dir = normalize(direction.x, direction.y)
  if (dir.len < 1e-6 || speed <= 0) return false
  cue.vx = dir.x * speed
  cue.vy = dir.y * speed
  return true
}

export const isSimulationIdle = (state: SimState, config: TableConfig = DEFAULT_TABLE) =>
  state.balls.every((ball) => !ball.active || hypot(ball.vx, ball.vy) <= config.stopSpeed)

export const stepSimulation = (
  state: SimState,
  dt: number,
  config: TableConfig = DEFAULT_TABLE
): SimState => {
  const next: SimState = {
    time: state.time + dt,
    balls: state.balls.map((ball) => ({ ...ball }))
  }

  for (const ball of next.balls) {
    if (!ball.active) continue
    ball.x += ball.vx * dt
    ball.y += ball.vy * dt
    applyRollingFriction(ball, dt, config.rollingFriction, config.stopSpeed)
  }

  for (let i = 0; i < next.balls.length; i += 1) {
    for (let j = i + 1; j < next.balls.length; j += 1) {
      resolveBallPair(next.balls[i], next.balls[j])
    }
  }

  for (const ball of next.balls) {
    if (!ball.active) continue
    tryPocket(ball, config, next.time)
    if (!ball.active) continue
    resolveWall(ball, config, next.time)
    if (!ball.active) continue
    tryPocket(ball, config, next.time)
  }

  return next
}

/** Run fixed-timestep simulation until idle or timeout. */
export const simulateUntilIdle = (
  state: SimState,
  options?: {
    config?: TableConfig
    fixedDt?: number
    maxSteps?: number
  }
): SimState => {
  const config = options?.config ?? DEFAULT_TABLE
  const fixedDt = options?.fixedDt ?? 1 / 120
  const maxSteps = options?.maxSteps ?? 12000

  let current = state
  let steps = 0
  while (!isSimulationIdle(current, config) && steps < maxSteps) {
    current = stepSimulation(current, fixedDt, config)
    steps += 1
  }
  return current
}

export const directionBetween = (from: Point2D, to: Point2D): Point2D => ({
  x: to.x - from.x,
  y: to.y - from.y
})
