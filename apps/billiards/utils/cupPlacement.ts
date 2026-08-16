import type { CupFormat, CupMatch } from '~/types/cup'
import { nextPowerOfTwo } from '~/types/cup'

const isDecisiveFinal = (match: CupMatch) =>
  match.roundKey === 'de-final' || match.roundKey === 'grand-final'

/** Players still in the bracket at this round (64 → first round has 64, etc.). */
export const playersInRound = (match: CupMatch): number | null => {
  if (isDecisiveFinal(match)) return 2
  if (match.roundKey === 'wb-final' || match.roundKey === 'se-final') return 2
  if (match.roundKey === 'wb-semi') return 4
  if (match.roundKey.startsWith('wb2-')) return null
  const upper = match.roundKey.match(/^se-r(\d+)$/)
  if (upper) return Number(upper[1])
  return null
}

export const bracketSizeFromMatches = (matches: CupMatch[], playerCount: number, format: CupFormat) => {
  const upper = matches
    .map((match) => playersInRound(match))
    .filter((value): value is number => value != null)
  const max = upper.length ? Math.max(...upper) : playerCount
  return nextPowerOfTwo(Math.max(playerCount, max, format === 'de' ? 4 : 2))
}

/** Placement range for the loser of this match (bill4you-style). */
export const matchPlacementLabel = (
  match: CupMatch,
  matches: CupMatch[],
  playerCount: number,
  format: CupFormat
): string | null => {
  if (isDecisiveFinal(match) || (format === 'se' && match.bracketSide === 'final')) {
    return 'место 1–2'
  }

  if (match.roundKey === 'wb-semi') return 'место 3–4'
  if (match.roundKey === 'wb-final') return 'место 3–4'
  if (match.roundKey === 'lb-final') return 'место 3–4'

  const inRound = playersInRound(match)
  if (inRound && match.bracketSide === 'winners') {
    const lo = inRound / 2 + 1
    const hi = inRound
    return `место ${lo}–${hi}`
  }

  if (match.roundKey.startsWith('wb2-')) {
    const size = bracketSizeFromMatches(matches, playerCount, format)
    const lo = Math.max(3, size / 4 + 1)
    return `место ${lo}–${size / 2}`
  }

  if (match.bracketSide === 'losers') {
    const size = bracketSizeFromMatches(matches, playerCount, format)
    if (match.roundKey === 'lb-r1') {
      const lo = size / 2 + 1
      return `место ${lo}–${size}`
    }
    if (match.roundKey === 'lb-final' || match.roundKey.startsWith('lb-r')) {
      const lo = size / 4 + 1
      const hi = size / 2
      return `место ${lo}–${hi}`
    }
  }

  return null
}

export const matchRoutingHint = (match: CupMatch, matches: CupMatch[]): string | null => {
  const parts: string[] = []
  if (match.nextMatchId) {
    const next = matches.find((item) => item.id === match.nextMatchId)
    if (next?.displayNo) parts.push(`побед. #${next.displayNo}`)
  }
  if (match.loserNextMatchId) {
    const next = matches.find((item) => item.id === match.loserNextMatchId)
    if (next?.displayNo) parts.push(`проигр. #${next.displayNo}`)
  }
  return parts.length ? parts.join(' · ') : null
}
