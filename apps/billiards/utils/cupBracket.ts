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
 * Classic double-elimination (Challonge / billiard DE):
 * — full winners bracket to WB final;
 * — losers bracket with crossover so a player who drops does not
 *   immediately rematch the opponent who just beat them (except grand final);
 * — grand final: WB champion vs LB champion.
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

  const isByeMatch = (match: CupMatch) => match.status === 'done' && !match.playerBId

  /** Reverse index — standard DE crossover between halves. */
  const crossover = (index: number, count: number) => count - 1 - index

  // --- Winners bracket (full SE tree) ---
  const wbRounds: CupMatch[][] = []

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
  wbRounds.push(r1)

  let prevWb = r1
  let matchesInRound = size / 2
  while (matchesInRound > 1) {
    const nextCount = matchesInRound / 2
    const isWbFinal = nextCount === 1
    const bracketPlayers = nextCount * 2
    const round: CupMatch[] = []
    for (let i = 0; i < nextCount; i += 1) {
      round.push(
        pushMatch({
          id: cupUid('m'),
          roundKey: isWbFinal ? 'wb-final' : `se-r${bracketPlayers}`,
          roundLabel: isWbFinal ? 'Верхняя · финал' : roundLabelSe(bracketPlayers, false),
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
    for (let i = 0; i < prevWb.length; i += 1) {
      const target = round[Math.floor(i / 2)]
      prevWb[i].nextMatchId = target.id
      prevWb[i].nextSlot = i % 2 === 0 ? 'A' : 'B'
    }
    wbRounds.push(round)
    prevWb = round
    matchesInRound = nextCount
  }

  // --- Losers bracket ---
  // Sources feeding the next LB column: LB match winners or a direct R1 loser (BYE skip).
  type LbSource =
    | { type: 'match'; match: CupMatch }
    | { type: 'r1-loser'; match: CupMatch }

  let lbSources: (LbSource | null)[] = []
  let lbRoundNo = 1

  // LB R1: adjacent WB R1 losers (skip BYE feeders; keep null slots for alignment).
  const r1Pairs = wbRounds[0].length / 2
  for (let i = 0; i < r1Pairs; i += 1) {
    const feederA = wbRounds[0][i * 2]
    const feederB = wbRounds[0][i * 2 + 1]
    const live = [feederA, feederB].filter((match) => !isByeMatch(match))

    if (live.length === 2) {
      const lb = pushMatch({
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
      feederA.loserNextMatchId = lb.id
      feederA.loserNextSlot = 'A'
      feederB.loserNextMatchId = lb.id
      feederB.loserNextSlot = 'B'
      lbSources.push({ type: 'match', match: lb })
    } else if (live.length === 1) {
      lbSources.push({ type: 'r1-loser', match: live[0] })
      for (const feeder of [feederA, feederB]) {
        if (isByeMatch(feeder)) {
          feeder.loserNextMatchId = null
          feeder.loserNextSlot = null
        }
      }
    } else {
      feederA.loserNextMatchId = null
      feederA.loserNextSlot = null
      feederB.loserNextMatchId = null
      feederB.loserNextSlot = null
      lbSources.push(null)
    }
  }
  lbRoundNo = 2

  // For each later WB round: drop-in with crossover, then optional consolidation.
  for (let r = 1; r < wbRounds.length; r += 1) {
    const wbRound = wbRounds[r]
    const dropCount = wbRound.length
    const isLastWb = r === wbRounds.length - 1
    const sources: (LbSource | null)[] = Array.from(
      { length: dropCount },
      (_, i) => lbSources[i] ?? null
    )

    const dropRound: CupMatch[] = []
    for (let i = 0; i < dropCount; i += 1) {
      const isLbFinal = isLastWb && dropCount === 1
      const drop = pushMatch({
        id: cupUid('m'),
        roundKey: isLbFinal ? 'lb-final' : `lb-r${lbRoundNo}`,
        roundLabel: isLbFinal ? 'Нижняя · финал' : `Нижняя · тур ${lbRoundNo}`,
        bracketSide: 'losers',
        order: i,
        playerAId: null,
        playerBId: null,
        nextMatchId: null,
        nextSlot: null,
        loserNextMatchId: null,
        loserNextSlot: null
      })
      dropRound.push(drop)

      const src = sources[i]
      if (src?.type === 'match') {
        src.match.nextMatchId = drop.id
        src.match.nextSlot = 'A'
      } else if (src?.type === 'r1-loser') {
        src.match.loserNextMatchId = drop.id
        src.match.loserNextSlot = 'A'
      }

      const wbLoserFrom = wbRound[crossover(i, dropCount)]
      wbLoserFrom.loserNextMatchId = drop.id
      wbLoserFrom.loserNextSlot = 'B'
    }

    if (!(isLastWb && dropCount === 1)) {
      lbRoundNo += 1
    }

    let nextSources: (LbSource | null)[] = dropRound.map((match) => ({
      type: 'match' as const,
      match
    }))

    if (!isLastWb && dropRound.length > 1) {
      const consCount = dropRound.length / 2
      const consRound: CupMatch[] = []
      for (let i = 0; i < consCount; i += 1) {
        const cons = pushMatch({
          id: cupUid('m'),
          roundKey: `lb-r${lbRoundNo}`,
          roundLabel: `Нижняя · тур ${lbRoundNo}`,
          bracketSide: 'losers',
          order: i,
          playerAId: null,
          playerBId: null,
          nextMatchId: null,
          nextSlot: null,
          loserNextMatchId: null,
          loserNextSlot: null
        })
        consRound.push(cons)
        dropRound[i * 2].nextMatchId = cons.id
        dropRound[i * 2].nextSlot = 'A'
        dropRound[i * 2 + 1].nextMatchId = cons.id
        dropRound[i * 2 + 1].nextSlot = 'B'
      }
      lbRoundNo += 1
      nextSources = consRound.map((match) => ({ type: 'match' as const, match }))
    }

    lbSources = nextSources
  }

  // Grand final: undefeated WB champion vs LB champion.
  const wbFinal = wbRounds[wbRounds.length - 1][0]
  const lbChampionSource = lbSources.find((src) => src != null) ?? null
  const grand = pushMatch({
    id: cupUid('m'),
    roundKey: 'de-final',
    roundLabel: 'Финал',
    bracketSide: 'final',
    order: 0,
    playerAId: null,
    playerBId: null,
    nextMatchId: null,
    nextSlot: null,
    loserNextMatchId: null,
    loserNextSlot: null
  })
  wbFinal.nextMatchId = grand.id
  wbFinal.nextSlot = 'A'
  if (lbChampionSource?.type === 'match') {
    lbChampionSource.match.nextMatchId = grand.id
    lbChampionSource.match.nextSlot = 'B'
  } else if (lbChampionSource?.type === 'r1-loser') {
    lbChampionSource.match.loserNextMatchId = grand.id
    lbChampionSource.match.loserNextSlot = 'B'
  }

  for (const match of matches) {
    if (match.status !== 'done' || !match.winnerId) continue
    placePlayer(matches, match.nextMatchId, match.nextSlot, match.winnerId)
  }

  resolveSinglePlayerByes(matches)

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

/** True if some unfinished match still feeds this slot. */
const slotStillFed = (matches: CupMatch[], matchId: string, slot: MatchSlot) =>
  matches.some(
    (match) =>
      match.status !== 'done' &&
      ((match.nextMatchId === matchId && match.nextSlot === slot) ||
        (match.loserNextMatchId === matchId && match.loserNextSlot === slot))
  )

/**
 * Auto-complete matches that have exactly one player and no pending feeder
 * for the empty slot (BYE through lower bracket after padding).
 */
const resolveSinglePlayerByes = (matches: CupMatch[]) => {
  let changed = true
  while (changed) {
    changed = false
    for (const match of matches) {
      if (match.status === 'done') continue
      const hasA = Boolean(match.playerAId)
      const hasB = Boolean(match.playerBId)
      if (hasA === hasB) continue
      if (hasA && slotStillFed(matches, match.id, 'B')) continue
      if (hasB && slotStillFed(matches, match.id, 'A')) continue

      const winnerId = (match.playerAId || match.playerBId)!
      if (!match.playerAId && match.playerBId) {
        match.playerAId = match.playerBId
        match.playerBId = null
      }
      match.winnerId = winnerId
      match.status = 'done'
      placePlayer(matches, match.nextMatchId, match.nextSlot, winnerId)
      changed = true
    }
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

  const loserId = winnerId === match.playerAId ? match.playerBId : match.playerAId

  match.winnerId = winnerId
  match.status = 'done'
  match.ballsA = 0
  match.ballsB = 0

  placePlayer(matches, match.nextMatchId, match.nextSlot, winnerId)

  if (format === 'de' && loserId) {
    placePlayer(matches, match.loserNextMatchId, match.loserNextSlot, loserId)
  }

  resolveSinglePlayerByes(matches)

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
