import type { CupFormat, CupMatch } from '~/types/cup'

export const BRACKET_CARD_W = 220
export const BRACKET_CARD_H = 112
export const BRACKET_ROW_STEP = 128
export const BRACKET_COL_GAP = 72
export const BRACKET_BAND_GAP = 56
export const BRACKET_COL_HEADER = 28
export const BRACKET_PAD = 20

export type BracketLayoutNode = {
  match: CupMatch
  x: number
  y: number
  band: 'upper' | 'lower'
  columnLabel: string | null
}

export type BracketLayoutConnector = {
  id: string
  path: string
  kind: 'winner' | 'loser'
}

export type BracketLayout = {
  width: number
  height: number
  nodes: BracketLayoutNode[]
  connectors: BracketLayoutConnector[]
  upperBandY: number
  lowerBandY: number | null
}

const isDecisiveFinal = (match: CupMatch) =>
  match.roundKey === 'de-final' || match.roundKey === 'grand-final'

const roundSortKey = (roundKey: string) => {
  if (roundKey === 'de-final' || roundKey === 'grand-final') return 50_000
  if (roundKey === 'wb-semi') return 40_000
  if (roundKey === 'wb-final' || roundKey === 'se-final') return 40_000
  const wb2 = roundKey.match(/^wb2-(\d+)$/)
  if (wb2) return 10_000 - Number(wb2[1]) + 1
  const upper = roundKey.match(/^se-r(\d+)$/)
  if (upper) return 10_000 - Number(upper[1])
  if (roundKey === 'lb-final') return 9_000
  const lower = roundKey.match(/^lb-r(\d+)$/)
  if (lower) return Number(lower[1]) * 100
  return 5_000
}

const columnsFromMatches = (matches: CupMatch[]): CupMatch[][] => {
  const keys = [...new Set(matches.map((match) => match.roundKey))].sort(
    (a, b) => roundSortKey(a) - roundSortKey(b)
  )
  return keys.map((key) =>
    matches.filter((match) => match.roundKey === key).sort((a, b) => a.order - b.order)
  )
}

/** Push cards apart so they never overlap inside one column. */
const resolveColumnOverlaps = (
  nodes: BracketLayoutNode[],
  positions: Map<string, { x: number; y: number }>
) => {
  const byX = new Map<number, BracketLayoutNode[]>()
  for (const node of nodes) {
    const list = byX.get(node.x) || []
    list.push(node)
    byX.set(node.x, list)
  }

  for (const list of byX.values()) {
    list.sort((a, b) => a.y - b.y || a.match.order - b.match.order)
    for (let i = 1; i < list.length; i += 1) {
      const prev = list[i - 1]
      const minY = prev.y + BRACKET_ROW_STEP
      if (list[i].y < minY) {
        list[i].y = minY
        positions.set(list[i].match.id, { x: list[i].x, y: list[i].y })
      }
    }
  }
}

const layoutColumns = (
  columns: CupMatch[][],
  startY: number,
  band: 'upper' | 'lower'
): { nodes: BracketLayoutNode[]; height: number } => {
  if (!columns.length) return { nodes: [], height: 0 }

  const nodes: BracketLayoutNode[] = []
  const positions = new Map<string, { x: number; y: number }>()
  const contentTop = startY + (band === 'upper' ? BRACKET_COL_HEADER + 8 : BRACKET_COL_HEADER)

  columns.forEach((colMatches, colIndex) => {
    const x = BRACKET_PAD + colIndex * (BRACKET_CARD_W + BRACKET_COL_GAP)

    if (colIndex === 0) {
      colMatches.forEach((match, rowIndex) => {
        const y = contentTop + rowIndex * BRACKET_ROW_STEP
        positions.set(match.id, { x, y })
        nodes.push({
          match,
          x,
          y,
          band,
          columnLabel: isDecisiveFinal(match) ? 'Финал' : null
        })
      })
      return
    }

    colMatches.forEach((match, rowIndex) => {
      const winnerFeeders = columns[colIndex - 1].filter((prev) => prev.nextMatchId === match.id)
      const anyFeeders = columns[colIndex - 1].filter(
        (prev) => prev.nextMatchId === match.id || prev.loserNextMatchId === match.id
      )

      let y: number
      if (winnerFeeders.length >= 2) {
        const a = positions.get(winnerFeeders[0].id)
        const b = positions.get(winnerFeeders[1].id)
        y = a && b ? (a.y + b.y) / 2 : contentTop + rowIndex * BRACKET_ROW_STEP
      } else if (winnerFeeders.length === 1) {
        const a = positions.get(winnerFeeders[0].id)
        y = a ? a.y : contentTop + rowIndex * BRACKET_ROW_STEP
      } else if (anyFeeders.length >= 1) {
        const ys = anyFeeders
          .map((item) => positions.get(item.id)?.y)
          .filter((value): value is number => value != null)
        y = ys.length ? ys.reduce((sum, value) => sum + value, 0) / ys.length : contentTop + rowIndex * BRACKET_ROW_STEP
      } else {
        y = contentTop + rowIndex * BRACKET_ROW_STEP
      }

      positions.set(match.id, { x, y })
      nodes.push({
        match,
        x,
        y,
        band,
        columnLabel: isDecisiveFinal(match) ? 'Финал' : null
      })
    })
  })

  resolveColumnOverlaps(nodes, positions)

  const maxY = nodes.reduce((acc, node) => Math.max(acc, node.y + BRACKET_CARD_H), startY)
  return { nodes, height: maxY - startY + BRACKET_PAD }
}

const elbowPath = (fromX: number, fromY: number, toX: number, toY: number) => {
  const midX = fromX + (toX - fromX) / 2
  return `M ${fromX} ${fromY} L ${midX} ${fromY} L ${midX} ${toY} L ${toX} ${toY}`
}

export const buildBracketLayout = (matches: CupMatch[], format: CupFormat): BracketLayout => {
  const upperMatches = matches.filter(
    (match) =>
      match.bracketSide === 'winners' ||
      isDecisiveFinal(match) ||
      (format === 'se' && match.bracketSide === 'final')
  )
  const lowerMatches = matches.filter((match) => match.bracketSide === 'losers')

  const upperColumns = columnsFromMatches(upperMatches)
  const lowerColumns = columnsFromMatches(lowerMatches)

  const upperStart = BRACKET_PAD
  const upper = layoutColumns(upperColumns, upperStart, 'upper')
  const lowerStart = upperStart + upper.height + (lowerColumns.length ? BRACKET_BAND_GAP : 0)
  const lower = layoutColumns(lowerColumns, lowerStart, 'lower')

  const nodes = [...upper.nodes, ...lower.nodes]
  const byId = new Map(nodes.map((node) => [node.match.id, node]))

  const connectors: BracketLayoutConnector[] = []
  for (const node of nodes) {
    const match = node.match
    if (match.nextMatchId) {
      const target = byId.get(match.nextMatchId)
      if (target) {
        connectors.push({
          id: `w-${match.id}`,
          kind: 'winner',
          path: elbowPath(
            node.x + BRACKET_CARD_W,
            node.y + BRACKET_CARD_H / 2,
            target.x,
            target.y + BRACKET_CARD_H / 2
          )
        })
      }
    }
    if (match.loserNextMatchId) {
      const target = byId.get(match.loserNextMatchId)
      if (target) {
        connectors.push({
          id: `l-${match.id}`,
          kind: 'loser',
          path: elbowPath(
            node.x + BRACKET_CARD_W,
            node.y + BRACKET_CARD_H - 18,
            target.x,
            target.y + BRACKET_CARD_H / 2
          )
        })
      }
    }
  }

  const width =
    nodes.reduce((acc, node) => Math.max(acc, node.x + BRACKET_CARD_W), 0) + BRACKET_PAD * 2
  const height =
    nodes.reduce((acc, node) => Math.max(acc, node.y + BRACKET_CARD_H), 0) + BRACKET_PAD * 2

  return {
    width: Math.max(width, 480),
    height: Math.max(height, 280),
    nodes,
    connectors,
    upperBandY: upperStart,
    lowerBandY: lowerColumns.length ? lowerStart : null
  }
}

/** Only «Финал» — directly above the final card. */
export const columnHeaders = (layout: BracketLayout) =>
  layout.nodes
    .filter((node) => node.columnLabel)
    .map((node) => ({
      x: node.x,
      y: Math.max(BRACKET_PAD, node.y - BRACKET_COL_HEADER),
      label: node.columnLabel as string
    }))
