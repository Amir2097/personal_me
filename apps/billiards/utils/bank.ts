import type { BuyInKind, BuyInRecord } from '~/types/kolkhoz'

export const buyInKindLabel = (kind: BuyInKind) => {
  if (kind === 'entry') return 'Взнос'
  if (kind === 'rebuy') return 'Докуп'
  if (kind === 'addon') return 'Дон / аддон'
  return kind
}

export const sumMoney = (buyIns: BuyInRecord[]) =>
  buyIns.reduce((sum, item) => sum + (Number(item.money) || 0), 0)

export const sumChips = (buyIns: BuyInRecord[]) =>
  buyIns.reduce((sum, item) => sum + (Number(item.chips) || 0), 0)

export const buyInsForPlayer = (buyIns: BuyInRecord[], playerId: string) =>
  buyIns.filter((item) => item.playerId === playerId)

export const playerPaid = (buyIns: BuyInRecord[], playerId: string) =>
  sumMoney(buyInsForPlayer(buyIns, playerId))

export const playerBoughtChips = (buyIns: BuyInRecord[], playerId: string) =>
  sumChips(buyInsForPlayer(buyIns, playerId))

/** Prize fund from total bank (rubles), rounded to whole currency units. */
export const calcPrizePool = (totalBank: number, prizePercent: number) => {
  const pct = Math.max(0, Math.min(100, prizePercent))
  return Math.round((totalBank * pct) / 100)
}

export const calcHouseCut = (totalBank: number, prizePercent: number) =>
  Math.max(0, Math.round(totalBank) - calcPrizePool(totalBank, prizePercent))

/**
 * Split prize pool by place shares (percent of prize pool).
 * Shares that don't sum to 100 still work proportionally to their sum.
 */
export const splitPrizes = (
  prizePool: number,
  places: { place: number; percent: number }[]
): { place: number; percent: number; amount: number }[] => {
  const active = places.filter((p) => p.percent > 0)
  const weight = active.reduce((sum, p) => sum + p.percent, 0) || 1
  return places.map((p) => ({
    place: p.place,
    percent: p.percent,
    amount: p.percent > 0 ? Math.round((prizePool * p.percent) / weight) : 0
  }))
}
