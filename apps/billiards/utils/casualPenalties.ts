import type { CasualPartyState, CasualPenaltyConfig, Player } from '~/types/kolkhoz'
import type { ScoreEvent } from '~/types/kolkhoz'

const uid = () =>
  typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `id_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`

export const playerStakePrice = (player: Player, tableBallPrice: number): number => {
  const stake = (player as Player & { stakePrice?: number }).stakePrice
  if (typeof stake === 'number' && stake > 0) return Math.round(stake)
  return tableBallPrice
}

export const nextPlayerInCircle = (orderedIds: string[], playerId: string): string | null => {
  const index = orderedIds.indexOf(playerId)
  if (index < 0 || orderedIds.length < 2) return null
  return orderedIds[(index + 1) % orderedIds.length] ?? null
}

export const playerPottedTotal = (party: CasualPartyState, playerId: string): number => {
  const rack = party.rackPointsByPlayer[playerId] || 0
  const extra = party.extraPointsByPlayer[playerId] || 0
  return rack + extra
}

/** Remove one potted-ball unit from player tally (rack first). */
export const removeOnePottedBall = (
  party: CasualPartyState,
  playerId: string
): { party: CasualPartyState; removed: boolean } => {
  const rack = party.rackPointsByPlayer[playerId] || 0
  if (rack >= 1) {
    const nextRack = { ...party.rackPointsByPlayer }
    nextRack[playerId] = rack - 1
    if (nextRack[playerId] <= 0) delete nextRack[playerId]
    return {
      removed: true,
      party: {
        ...party,
        rackPointsByPlayer: nextRack,
        rackPointsTotal: Math.max(0, party.rackPointsTotal - 1)
      }
    }
  }

  const extra = party.extraPointsByPlayer[playerId] || 0
  if (extra >= 1) {
    const nextExtra = { ...party.extraPointsByPlayer }
    nextExtra[playerId] = extra - 1
    if (nextExtra[playerId] <= 0) delete nextExtra[playerId]
    return {
      removed: true,
      party: { ...party, extraPointsByPlayer: nextExtra }
    }
  }

  return { party, removed: false }
}

export type ApplyCasualFoulResult = {
  party: CasualPartyState
  players: Player[]
  event: ScoreEvent
  amountEach?: number
}

export const applyCasualFoul = (
  party: CasualPartyState,
  players: Player[],
  tablePlayerIds: string[],
  offenderId: string,
  config: CasualPenaltyConfig,
  tableBallPrice: number,
  tableId: string
): ApplyCasualFoulResult => {
  const offender = players.find((player) => player.id === offenderId)
  if (!offender) throw new Error('Игрок не найден.')

  const activeIds = tablePlayerIds.filter((id) => {
    const player = players.find((item) => item.id === id)
    return player && player.status === 'active'
  })
  const opponents = activeIds.filter((id) => id !== offenderId)
  if (opponents.length < 1) throw new Error('Нужно минимум 2 игрока за столом.')

  // Snapshot is needed for undo + history. In browser `structuredClone` may fail
  // if `party` contains non-cloneable objects (e.g. from reactive wrappers).
  const partySnapshot = (() => {
    try {
      return structuredClone(party)
    } catch {
      // Fallback: party is plain data, so JSON clone is safe here.
      return JSON.parse(JSON.stringify(party)) as CasualPartyState
    }
  })()

  if (config.mode === 'pay_all') {
    const amountEach = config.usePersonalStake
      ? playerStakePrice(offender, tableBallPrice)
      : tableBallPrice
    const total = amountEach * opponents.length
    const deltas: Record<string, number> = { [offenderId]: -total }
    for (const id of opponents) deltas[id] = amountEach

    const nextPlayers = players.map((player) => {
      const delta = deltas[player.id]
      if (delta === undefined) return player
      return { ...player, balance: player.balance + delta }
    })

    return {
      party,
      players: nextPlayers,
      amountEach,
      event: {
        id: uid(),
        at: new Date().toISOString(),
        mode: 'casual',
        tableId,
        scorerId: offenderId,
        ballId: 'foul',
        deltas,
        kind: 'casual_foul',
        note: `Фол · платит всем по ${amountEach} ₽ (${opponents.length} игр.)`,
        foulSnapshot: { party: partySnapshot, playerBalances: Object.fromEntries(players.map((p) => [p.id, p.balance])) }
      }
    }
  }

  if (config.mode === 'ball_from_home') {
    const { party: afterRemove, removed } = removeOnePottedBall(party, offenderId)
    let nextParty = afterRemove

    if (removed) {
      nextParty = { ...nextParty, ballsOnTable: (nextParty.ballsOnTable || 0) + 1 }
      return {
        party: nextParty,
        players,
        event: {
          id: uid(),
          at: new Date().toISOString(),
          mode: 'casual',
          tableId,
          scorerId: offenderId,
          ballId: 'foul',
          deltas: {},
          kind: 'casual_foul',
          note: 'Фол · шар из дома выставлен на стол',
          foulSnapshot: { party: partySnapshot }
        }
      }
    }

    const debt = { ...(nextParty.ballDebtByPlayer || {}) }
    debt[offenderId] = (debt[offenderId] || 0) + 1
    nextParty = { ...nextParty, ballDebtByPlayer: debt }

    return {
      party: nextParty,
      players,
      event: {
        id: uid(),
        at: new Date().toISOString(),
        mode: 'casual',
        tableId,
        scorerId: offenderId,
        ballId: 'foul',
        deltas: {},
        kind: 'casual_foul',
        note: 'Фол · долг: выставить шар после первого забитого',
        foulSnapshot: { party: partySnapshot }
      }
    }
  }

  // pass_advantage
  const nextId = nextPlayerInCircle(activeIds, offenderId)
  const nextParty: CasualPartyState = {
    ...party,
    freeShotForPlayerId: nextId
  }
  const nextName = players.find((player) => player.id === nextId)?.name || 'следующий'

  return {
    party: nextParty,
    players,
    event: {
      id: uid(),
      at: new Date().toISOString(),
      mode: 'casual',
      tableId,
      scorerId: offenderId,
      ballId: 'foul',
      deltas: {},
      kind: 'casual_foul',
      note: `Фол · свободный удар для ${nextName}`,
      foulSnapshot: { party: partySnapshot }
    }
  }
}

export const penaltyModeLabel = (mode: CasualPenaltyConfig['mode']): string => {
  if (mode === 'pay_all') return 'Платит всем за столом'
  if (mode === 'ball_from_home') return 'Шар из дома'
  return 'Переход хода + свободный удар'
}
