import type { CupFormat, MatchStatus } from '~/types/cup'

export const CUP_SE_MAX_PLAYERS = 64
export const CUP_DE_MAX_PLAYERS = 64

export const cupFormatTitle = (format: CupFormat | string) =>
  format === 'de' ? 'До двух поражений' : 'Олимпийская система'

export const cupFormatHint = (format: CupFormat | string) =>
  format === 'de'
    ? 'Проигравший падает в нижнюю сетку. Выбывает только после второго поражения. До 64 игроков (например 50 → сетка на 64 с пропусками).'
    : 'Проигравший сразу выбывает. До 64 игроков; нехватка мест дополняется пропуском тура.'

export const cupRaceLabel = (raceTo: number) => `До ${raceTo} ${partyWord(raceTo)}`

export const partyWord = (n: number) => {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return 'партии'
  return 'партий'
}

export const matchStatusLabel = (status: MatchStatus | string) => {
  switch (status) {
    case 'pending':
      return 'Ожидание'
    case 'ready':
      return 'Готов'
    case 'live':
      return 'Идёт'
    case 'done':
      return 'Готово'
    default:
      return status
  }
}

export const slotName = (id: string | null, playerName: string | null | undefined) => {
  if (playerName) return playerName
  if (!id) return 'Пропуск тура'
  return '—'
}
