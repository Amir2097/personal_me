import type { Player } from '~/types/kolkhoz'

export type DebtTransfer = {
  fromId: string
  toId: string
  amount: number
}

/** Greedy match debtors → creditors from session balances (₽). */
export const computeDebtTransfers = (
  players: Pick<Player, 'id' | 'balance'>[]
): DebtTransfer[] => {
  const creditors = players
    .filter((player) => player.balance > 0)
    .map((player) => ({ id: player.id, amount: player.balance }))
    .sort((a, b) => b.amount - a.amount)

  const debtors = players
    .filter((player) => player.balance < 0)
    .map((player) => ({ id: player.id, amount: -player.balance }))
    .sort((a, b) => b.amount - a.amount)

  const transfers: DebtTransfer[] = []
  let debtorIdx = 0
  let creditorIdx = 0

  while (debtorIdx < debtors.length && creditorIdx < creditors.length) {
    const debtor = debtors[debtorIdx]!
    const creditor = creditors[creditorIdx]!
    const pay = Math.min(debtor.amount, creditor.amount)
    if (pay > 0) {
      transfers.push({ fromId: debtor.id, toId: creditor.id, amount: Math.round(pay) })
    }
    debtor.amount -= pay
    creditor.amount -= pay
    if (debtor.amount <= 0) debtorIdx += 1
    if (creditor.amount <= 0) creditorIdx += 1
  }

  return transfers
}
