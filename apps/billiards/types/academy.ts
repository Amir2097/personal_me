export type ExerciseLevel = 1 | 2 | 3 | 4

export type ExerciseCategory =
  | 'чужие'
  | 'свояки'
  | 'выход'
  | 'отыгрыш'
  | 'контроль'
  | 'дуплеты'
  | 'особые'
  | 'серии'

export type BallKind = 'cue' | 'target'

export type LineStyle = 'solid' | 'dashed'

export type Point2D = {
  x: number
  y: number
}

export type CueHitPoint = {
  /** [-1..1], negative = left spin, positive = right spin */
  offset_x: number
  /** [-1..1], negative = top spin, positive = draw/back spin */
  offset_y: number
  hint: string
}

export type Ball = {
  id: string
  type: BallKind
  x: number
  y: number
  label: string
}

/** Aiming ghost (phantom) ball for cut-shot geometry. */
export type GhostBall = {
  x: number
  y: number
  label?: string
}

export type Trajectory = {
  from: Point2D
  to: Point2D
  style: LineStyle
  color: string
}

export type Exercise = {
  id: string
  title: string
  level: ExerciseLevel
  level_label: string
  category: ExerciseCategory
  description: string
  instructions: string[]
  target_reps: number
  cue_hit_point: CueHitPoint
  balls: Ball[]
  trajectories: Trajectory[]
  /** Optional phantom ball showing where cue aims on a cut. */
  ghost_ball?: GhostBall
  /**
   * Expected cue-ball stop point (for exercises like clapshtoss).
   * Coordinates use the same SVG coordinate system (0..100 x, 0..50 y).
   */
  expected_cue_stop?: Point2D
  /**
   * Allowed distance (in SVG units) from expected stop point to still count as a hit.
   * Default suggestion: ~2
   */
  cue_stop_tolerance?: number
  /** Enable interactive physics prototype for this exercise. */
  physics_demo?: boolean
}

export type ProgressLog = {
  exerciseId: string
  attempts: number
  made: number
  updatedAt: string
}
