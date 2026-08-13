import {
  cupUid,
  nextPowerOfTwo,
  type BracketSide,
  type CupFormat,
  type CupMatch,
  type CupPlayer,
  type MatchSlot
} from '~/types/cup'

const roundLabelSe = (roundSize: number, isFinal: boolean) => {
  if (isFinal || roundSize === 2) return 'Финал'
  if (roundSize === 4) return '1/2'
  if (roundSize === 8) return '1/4'
  if (roundSize === 16) return '1/8'
  if (roundSize === 32) return '1/16'
  if (roundSize === 64) return '1/32'
  return `1/${Math.max(1, roundSize / 2)}`
}

const emptyMatch = (partial: Omit<
  CupMatch,
  'framesA' | 'framesB' | 'ballsA' | 'ballsB' | 'winnerId' | 'status' | 'tableNo' | 'displayNo'
> & {
  tableNo?: number
  status?: CupMatch['status']
  displayNo?: number
}): CupMatch => ({
  framesA: 0,
  framesB: 0,
  ballsA: 0,
  ballsB: 0,
  winnerId: null,
  tableNo: partial.tableNo ?? 1,
  status: partial.status ?? 'pending',
  displayNo: partial.displayNo ?? 0,
  ...partial
})

/** Stable #1…N numbers in creation order (как на bill4you). */
export const assignDisplayNumbers = (matches: CupMatch[]): CupMatch[] =>
  matches.map((match, index) => ({ ...match, displayNo: index + 1 }))

/** Standard seeding positions for a power-of-two bracket (1 plays last seed, etc.). */
export const seedingOrder = (size: number): number[] => {
  if (size === 1) return [1]
  const prev = seedingOrder(size / 2)
  const out: number[] = []
  for (const seed of prev) {
    out.push(seed)
    out.push(size + 1 - seed)
  }
  return out
}

export const preparePlayers = (players: CupPlayer[], shuffle = false): CupPlayer[] => {
  const list = players.map((player, index) => ({
    ...player,
    seed: player.seed || index + 1
  }))
  if (shuffle) {
    for (let i = list.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[list[i], list[j]] = [list[j], list[i]]
    }
    return list.map((player, index) => ({ ...player, seed: index + 1 }))
  }
  return [...list].sort((a, b) => a.seed - b.seed)
}

export type BracketBuildResult = {
  players: CupPlayer[]
  matches: CupMatch[]
}

/**
 * Single-elimination bracket. Pads to next power of two with BYEs.
 * BYE matches are auto-completed (winner = present player).
 */
export const buildSingleElimination = (
  inputPlayers: CupPlayer[],
  options?: { minSize?: number }
): BracketBuildResult => {
  if (inputPlayers.length < 2) {
    throw new Error('Нужно минимум 2 игрока')
  }
  if (inputPlayers.length > 64) {
    throw new Error('Олимпийская система — до 64 игроков')
  }

  const players = preparePlayers(inputPlayers)
  const size = Math.max(options?.minSize ?? 2, nextPowerOfTwo(players.length))
  const seeds = seedingOrder(size)
  const slots: (CupPlayer | null)[] = seeds.map((seed) => players[seed - 1] ?? null)

  const matches: CupMatch[] = []
  let prevRoundIds: string[] = []

  // First round
  const firstRoundIds: string[] = []
  for (let i = 0; i < size / 2; i += 1) {
    const a = slots[i * 2]
    const b = slots[i * 2 + 1]
    const id = cupUid('m')
    firstRoundIds.push(id)

    let status: CupMatch['status'] = 'pending'
    let winnerId: string | null = null
    let playerAId = a?.id ?? null
    let playerBId = b?.id ?? null

    if (a && !b) {
      status = 'done'
      winnerId = a.id
    } else if (b && !a) {
      status = 'done'
      winnerId = b.id
      playerAId = b.id
      playerBId = null
    } else if (a && b) {
      status = 'ready'
    }

    matches.push(
      emptyMatch({
        id,
        roundKey: `se-r${size}`,
        roundLabel: roundLabelSe(size, size === 2),
        bracketSide: 'winners',
        order: i,
        playerAId,
        playerBId,
        status,
        winnerId,
        nextMatchId: null,
        nextSlot: null,
        loserNextMatchId: null,
        loserNextSlot: null
      })
    )
  }
  prevRoundIds = firstRoundIds
  let matchesInRound = size / 2

  while (matchesInRound > 1) {
    const nextCount = matchesInRound / 2
    const isFinal = nextCount === 1
    const bracketPlayers = nextCount * 2
    const roundIds: string[] = []
    for (let i = 0; i < nextCount; i += 1) {
      const id = cupUid('m')
      roundIds.push(id)
      matches.push(
        emptyMatch({
          id,
          roundKey: isFinal ? 'se-final' : `se-r${bracketPlayers}`,
          roundLabel: roundLabelSe(bracketPlayers, isFinal),
          bracketSide: isFinal ? 'final' : 'winners',
          order: i,
          playerAId: null,
          playerBId: null,
          nextMatchId: null,
          nextSlot: null,
          loserNextMatchId: null,
          loserNextSlot: null
        })
      )
    }

    for (let i = 0; i < prevRoundIds.length; i += 1) {
      const prev = matches.find((match) => match.id === prevRoundIds[i])!
      const next = matches.find((match) => match.id === roundIds[Math.floor(i / 2)])!
      const slot: MatchSlot = i % 2 === 0 ? 'A' : 'B'
      prev.nextMatchId = next.id
      prev.nextSlot = slot
      if (prev.status === 'done' && prev.winnerId) {
        if (slot === 'A') next.playerAId = prev.winnerId
        else next.playerBId = prev.winnerId
      }
    }

    for (const id of roundIds) {
      const match = matches.find((item) => item.id === id)!
      if (match.playerAId && match.playerBId) match.status = 'ready'
      else if (match.playerAId || match.playerBId) match.status = 'pending'
    }

    prevRoundIds = roundIds
    matchesInRound = nextCount
  }

  return { players, matches: assignDisplayNumbers(matches) }
}

/**
 * Double-elimination как на bill4you:
 * — размер сетки = ближайшая степень 2 (4 на 4 игроков, без фейковых 1/4);
 * — два тура верхней сетки;
 * — проигравшие идут в нижнюю и возвращаются во встречи «на вылет»;
 * — дальше олимпийка до финала (для 8: полуфинал ×2 → финал).
 */
export const buildDoubleElimination = (inputPlayers: CupPlayer[]): BracketBuildResult => {
  if (inputPlayers.length < 3) {
    throw new Error('Система до двух поражений — минимум 3 игрока')
  }
  if (inputPlayers.length > 64) {
    throw new Error('Система до двух поражений — до 64 игроков')
  }

  const players = preparePlayers(inputPlayers)
  const size = nextPowerOfTwo(players.length)
  const seeds = seedingOrder(size)
  const slots: (CupPlayer | null)[] = seeds.map((seed) => players[seed - 1] ?? null)
  const matches: CupMatch[] = []

  const pushMatch = (
    partial: Omit<
      CupMatch,
      'framesA' | 'framesB' | 'ballsA' | 'ballsB' | 'winnerId' | 'status' | 'tableNo' | 'displayNo'
    > & {
      status?: CupMatch['status']
      winnerId?: string | null
    }
  ) => {
    const row = emptyMatch(partial)
    matches.push(row)
    return row
  }

  // --- Верхняя: тур 1 ---
  const r1: CupMatch[] = []
  for (let i = 0; i < size / 2; i += 1) {
    const a = slots[i * 2]
    const b = slots[i * 2 + 1]
    let status: CupMatch['status'] = 'pending'
    let winnerId: string | null = null
    let playerAId = a?.id ?? null
    let playerBId = b?.id ?? null

    if (a && !b) {
      status = 'done'
      winnerId = a.id
    } else if (b && !a) {
      status = 'done'
      winnerId = b.id
      playerAId = b.id
      playerBId = null
    } else if (a && b) {
      status = 'ready'
    }

    r1.push(
      pushMatch({
        id: cupUid('m'),
        roundKey: `se-r${size}`,
        roundLabel: 'Первый тур',
        bracketSide: 'winners',
        order: i,
        playerAId,
        playerBId,
        status,
        winnerId,
        nextMatchId: null,
        nextSlot: null,
        loserNextMatchId: null,
        loserNextSlot: null
      })
    )
  }

  // --- Верхняя: тур 2 ---
  const r2Count = size / 4
  const r2: CupMatch[] = []
  for (let i = 0; i < r2Count; i += 1) {
    r2.push(
      pushMatch({
        id: cupUid('m'),
        roundKey: `wb2-${size}`,
        roundLabel: 'Тур 2',
        bracketSide: 'winners',
        order: i,
        playerAId: null,
        playerBId: null,
        nextMatchId: null,
        nextSlot: null,
        loserNextMatchId: null,
        loserNextSlot: null
      })
    )
  }

  for (let i = 0; i < r1.length; i += 1) {
    const target = r2[Math.floor(i / 2)]
    r1[i].nextMatchId = target.id
    r1[i].nextSlot = i % 2 === 0 ? 'A' : 'B'
  }

  // --- Нижняя: пары проигравших тура 1 ---
  const lbR1: CupMatch[] = []
  for (let i = 0; i < r2Count; i += 1) {
    lbR1.push(
      pushMatch({
        id: cupUid('m'),
        roundKey: 'lb-r1',
        roundLabel: 'Нижняя · тур 1',
        bracketSide: 'losers',
        order: i,
        playerAId: null,
        playerBId: null,
        nextMatchId: null,
        nextSlot: null,
        loserNextMatchId: null,
        loserNextSlot: null
      })
    )
  }
  for (let i = 0; i < r1.length; i += 1) {
    const target = lbR1[Math.floor(i / 2)]
    r1[i].loserNextMatchId = target.id
    r1[i].loserNextSlot = i % 2 === 0 ? 'A' : 'B'
  }

  // --- Нижняя: победители нижней + проигравшие тура 2 ---
  const lbDrop: CupMatch[] = []
  for (let i = 0; i < r2Count; i += 1) {
    lbDrop.push(
      pushMatch({
        id: cupUid('m'),
        roundKey: r2Count === 1 ? 'lb-final' : 'lb-r2',
        roundLabel: r2Count === 1 ? 'Нижняя · финал' : 'Нижняя · тур 2',
        bracketSide: 'losers',
        order: i,
        playerAId: null,
        playerBId: null,
        nextMatchId: null,
        nextSlot: null,
        loserNextMatchId: null,
        loserNextSlot: null
      })
    )
  }
  for (let i = 0; i < r2Count; i += 1) {
    lbR1[i].nextMatchId = lbDrop[i].id
    lbR1[i].nextSlot = 'A'
    r2[i].loserNextMatchId = lbDrop[i].id
    r2[i].loserNextSlot = 'B'
  }

  // --- Возврат в основную сетку и олимпийка до финала ---
  let current: CupMatch[] = []
  const reEntryCount = r2Count
  const reEntryPlayers = reEntryCount * 2

  for (let i = 0; i < reEntryCount; i += 1) {
    const isFinal = reEntryCount === 1
    current.push(
      pushMatch({
        id: cupUid('m'),
        roundKey: isFinal ? 'de-final' : reEntryCount === 2 ? 'wb-semi' : `se-r${reEntryPlayers}`,
        roundLabel: isFinal ? 'Финал' : reEntryCount === 2 ? 'Полуфинал' : roundLabelSe(reEntryPlayers, false),
        bracketSide: isFinal ? 'final' : 'winners',
        order: i,
        playerAId: null,
        playerBId: null,
        nextMatchId: null,
        nextSlot: null,
        loserNextMatchId: null,
        loserNextSlot: null
      })
    )
  }

  for (let i = 0; i < reEntryCount; i += 1) {
    r2[i].nextMatchId = current[i].id
    r2[i].nextSlot = 'A'
    lbDrop[i].nextMatchId = current[i].id
    lbDrop[i].nextSlot = 'B'
  }

  while (current.length > 1) {
    const nextCount = current.length / 2
    const isFinal = nextCount === 1
    const bracketPlayers = nextCount * 2
    const nextRound: CupMatch[] = []
    for (let i = 0; i < nextCount; i += 1) {
      nextRound.push(
        pushMatch({
          id: cupUid('m'),
          roundKey: isFinal ? 'de-final' : nextCount === 2 ? 'wb-semi' : `se-r${bracketPlayers}`,
          roundLabel: isFinal ? 'Финал' : nextCount === 2 ? 'Полуфинал' : roundLabelSe(bracketPlayers, false),
          bracketSide: isFinal ? 'final' : 'winners',
          order: i,
          playerAId: null,
          playerBId: null,
          nextMatchId: null,
          nextSlot: null,
          loserNextMatchId: null,
          loserNextSlot: null
        })
      )
    }
    for (let i = 0; i < current.length; i += 1) {
      const target = nextRound[Math.floor(i / 2)]
      current[i].nextMatchId = target.id
      current[i].nextSlot = i % 2 === 0 ? 'A' : 'B'
    }
    current = nextRound
  }

  for (const match of matches) {
    if (match.status !== 'done' || !match.winnerId) continue
    placePlayer(matches, match.nextMatchId, match.nextSlot, match.winnerId)
  }

  for (const match of matches) {
    if (match.playerAId && match.playerBId && match.status === 'pending') {
      match.status = 'ready'
    }
  }

  return { players, matches: assignDisplayNumbers(matches) }
}

export const buildBracket = (
  format: CupFormat,
  players: CupPlayer[],
  options?: { shuffle?: boolean }
): BracketBuildResult => {
  const prepared = preparePlayers(players, options?.shuffle)
  if (format === 'de') return buildDoubleElimination(prepared)
  return buildSingleElimination(prepared)
}

const placePlayer = (
  matches: CupMatch[],
  matchId: string | null,
  slot: MatchSlot | null,
  playerId: string
) => {
  if (!matchId || !slot) return
  const match = matches.find((item) => item.id === matchId)
  if (!match) return
  if (slot === 'A') match.playerAId = playerId
  else match.playerBId = playerId
  if (match.playerAId && match.playerBId && match.status === 'pending') {
    match.status = 'ready'
  }
}

export type AdvanceResult = {
  matches: CupMatch[]
  tournamentWinnerId: string | null
  completed: boolean
}

/** Record match winner and feed players into next bracket slots. */
export const advanceWinner = (
  matchesInput: CupMatch[],
  matchId: string,
  winnerId: string,
  format: CupFormat
): AdvanceResult => {
  const matches = matchesInput.map((match) => ({ ...match }))
  const match = matches.find((item) => item.id === matchId)
  if (!match) throw new Error('Матч не найден')
  if (match.status === 'done') {
    return { matches, tournamentWinnerId: null, completed: false }
  }
  if (winnerId !== match.playerAId && winnerId !== match.playerBId) {
    throw new Error('Победитель должен быть участником матча')
  }

  const loserId =
    winnerId === match.playerAId ? match.playerBId : match.playerAId

  match.winnerId = winnerId
  match.status = 'done'
  match.ballsA = 0
  match.ballsB = 0

  placePlayer(matches, match.nextMatchId, match.nextSlot, winnerId)

  if (format === 'de' && loserId) {
    placePlayer(matches, match.loserNextMatchId, match.loserNextSlot, loserId)
  }

  let tournamentWinnerId: string | null = null
  let completed = false

  if (
    match.roundKey === 'de-final' ||
    match.roundKey === 'grand-final' ||
    (format === 'se' && match.bracketSide === 'final')
  ) {
    tournamentWinnerId = winnerId
    completed = true
  } else if (format === 'se' && !match.nextMatchId) {
    tournamentWinnerId = winnerId
    completed = true
  }

  return { matches, tournamentWinnerId, completed }
}

export const matchesByRound = (matches: CupMatch[], side?: BracketSide) => {
  const filtered = side ? matches.filter((match) => match.bracketSide === side) : matches
  const keys: string[] = []
  for (const match of filtered) {
    if (!keys.includes(match.roundKey)) keys.push(match.roundKey)
  }
  return keys.map((key) => ({
    roundKey: key,
    label: filtered.find((match) => match.roundKey === key)?.roundLabel || key,
    matches: filtered.filter((match) => match.roundKey === key).sort((a, b) => a.order - b.order)
  }))
}
