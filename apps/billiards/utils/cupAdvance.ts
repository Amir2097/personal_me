import type { CupMatch } from '~/types/cup'

export const addBall = (match: CupMatch, side: 'A' | 'B'): CupMatch => {
  if (match.status === 'done') return match
  return {
    ...match,
    status: match.status === 'pending' || match.status === 'ready' ? 'live' : match.status,
    ballsA: side === 'A' ? match.ballsA + 1 : match.ballsA,
    ballsB: side === 'B' ? match.ballsB + 1 : match.ballsB
  }
}

export const undoBall = (match: CupMatch, side: 'A' | 'B'): CupMatch => {
  if (match.status === 'done') return match
  return {
    ...match,
    ballsA: side === 'A' ? Math.max(0, match.ballsA - 1) : match.ballsA,
    ballsB: side === 'B' ? Math.max(0, match.ballsB - 1) : match.ballsB
  }
}

/** Award frame to a side; clears ball counters. Returns whether raceTo is reached. */
export const awardFrame = (
  match: CupMatch,
  side: 'A' | 'B',
  raceTo: number
): { match: CupMatch; raceWon: boolean; winnerId: string | null } => {
  if (match.status === 'done') {
    return { match, raceWon: false, winnerId: null }
  }
  const framesA = side === 'A' ? match.framesA + 1 : match.framesA
  const framesB = side === 'B' ? match.framesB + 1 : match.framesB
  const next: CupMatch = {
    ...match,
    framesA,
    framesB,
    ballsA: 0,
    ballsB: 0,
    status: 'live'
  }
  if (framesA >= raceTo && match.playerAId) {
    return { match: next, raceWon: true, winnerId: match.playerAId }
  }
  if (framesB >= raceTo && match.playerBId) {
    return { match: next, raceWon: true, winnerId: match.playerBId }
  }
  return { match: next, raceWon: false, winnerId: null }
}
