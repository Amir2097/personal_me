import * as XLSX from 'xlsx'
import type { CupState } from '~/types/cup'
import { cupFormatTitle, cupRaceLabel, matchStatusLabel } from '~/utils/cupLabels'

export const buildCupWorkbook = (state: CupState): XLSX.WorkBook => {
  const wb = XLSX.utils.book_new()
  const tournament = state.tournament
  const winnerName =
    state.players.find((player) => player.id === tournament.winnerId)?.name || '—'

  const summary = [
    ['Поле', 'Значение'],
    ['Турнир', tournament.name],
    ['Формат', cupFormatTitle(tournament.format)],
    ['До побед', cupRaceLabel(tournament.raceTo)],
    ['Статус', tournament.status],
    ['Игроков', state.players.length],
    ['Матчей', state.matches.length],
    ['Сыграно', state.matches.filter((match) => match.status === 'done').length],
    ['Победитель', winnerName],
    ['Создан', tournament.createdAt || '—'],
    ['Завершён', tournament.completedAt || '—']
  ]
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(summary), 'Сводка')

  const players = [
    ['Посев', 'Имя', 'Логин аккаунта'],
    ...state.players.map((player) => [player.seed, player.name, player.username || ''])
  ]
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(players), 'Игроки')

  const playerName = (id: string | null) =>
    id ? state.players.find((player) => player.id === id)?.name || id : '—'

  const matches = [
    ['№', 'Раунд', 'Сторона', 'Игрок A', 'Игрок B', 'Партии', 'Шары', 'Статус', 'Победитель'],
    ...state.matches.map((match) => [
      match.displayNo,
      match.roundLabel,
      match.bracketSide,
      playerName(match.playerAId),
      playerName(match.playerBId),
      `${match.framesA}:${match.framesB}`,
      `${match.ballsA}:${match.ballsB}`,
      matchStatusLabel(match.status),
      playerName(match.winnerId)
    ])
  ]
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(matches), 'Матчи')

  return wb
}

export const downloadCupExcel = (state: CupState, filename?: string) => {
  const wb = buildCupWorkbook(state)
  const safeName = (state.tournament.name || 'cup')
    .replace(/[^\w\u0400-\u04FF-]+/g, '_')
    .slice(0, 40)
  const name = filename || `${safeName}-${new Date().toISOString().slice(0, 10)}.xlsx`
  XLSX.writeFile(wb, name)
}
