import { groupLabel, modeLabel, tournamentKindLabel } from '~/utils/labels'
import { buyInKindLabel, calcHouseCut, calcPrizePool, playerPaid, splitPrizes, sumMoney } from '~/utils/bank'
import * as XLSX from 'xlsx'
import type { KolkhozState } from '~/types/kolkhoz'

const kindLabel = (kind: string | undefined) => {
  if (kind === 'organizer') return 'Организаторская'
  if (kind === 'detailed') return 'Подробная игра'
  return tournamentKindLabel(kind)
}

/** Build a multi-sheet .xlsx workbook from Kolkhoz session state. */
export const buildKolkhozWorkbook = (state: KolkhozState): XLSX.WorkBook => {
  const wb = XLSX.utils.book_new()
  const buyIns = state.tournament.buyIns || []
  const bankTotal = sumMoney(buyIns)
  const prizePercent = state.tournament.bank?.prizePercent ?? 80
  const prizes = calcPrizePool(bankTotal, prizePercent)

  const summary = [
    ['Поле', 'Значение'],
    ['Режим', modeLabel(state.mode)],
    ['Вид турнира', state.mode === 'tournament' ? kindLabel(state.tournament.kind) : '—'],
    ['Игроков', state.players.length],
    ['Активных', state.players.filter((p) => p.status === 'active').length],
    ['Событий', state.events.length],
    ['Текущий тур', state.tournament.rounds[state.tournament.currentRoundIndex]?.number ?? '—'],
    ['Столов', state.tournament.tableCount],
    ['Банк, ₽', bankTotal],
    ['Призовые %', prizePercent],
    ['Призовые, ₽', prizes],
    ['Остаток, ₽', calcHouseCut(bankTotal, prizePercent)],
    ['Обновлено', state.updatedAt]
  ]
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(summary), 'Сводка')

  const players = [
    ['Имя', 'Группа', 'Фора', 'Старт', 'Фишки', 'Внёс, ₽', 'Статус'],
    ...state.players.map((p) => [
      p.name,
      groupLabel(p.category),
      p.handicap,
      p.startingStack,
      p.balance,
      playerPaid(buyIns, p.id),
      p.status === 'eliminated' ? 'вне игры' : 'в игре'
    ])
  ]
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(players), 'Игроки')

  const tableRows: (string | number)[][] = [['Стол', '№ в зале', 'Место', 'Игрок', 'Группа', 'Фишки', 'Статус']]
  for (const table of state.tournament.tables) {
    table.playerIds.forEach((id, index) => {
      const player = state.players.find((p) => p.id === id)
      tableRows.push([
        table.label,
        table.number ?? '',
        index + 1,
        player?.name || id,
        player ? groupLabel(player.category) : '',
        player?.balance ?? '',
        player ? (player.status === 'eliminated' ? 'вне игры' : 'в игре') : ''
      ])
    })
    if (!table.playerIds.length) {
      tableRows.push([table.label, table.number ?? '', '', '—', '', '', ''])
    }
  }
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(tableRows), 'Столы')

  const rounds = [
    ['Тур', 'Минут', 'Группа 1', 'Группа 2', 'Группа 3', 'Текущий'],
    ...state.tournament.rounds.map((round, index) => [
      round.number,
      round.durationMinutes,
      round.tariffs[1],
      round.tariffs[2],
      round.tariffs[3],
      index === state.tournament.currentRoundIndex ? 'да' : ''
    ])
  ]
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(rounds), 'Туры')

  const events = [
    ['Время', 'Тип', 'Забил / игрок', 'У кого / заметка', 'Переводы'],
    ...state.events.map((event) => {
      const scorer = state.players.find((p) => p.id === event.scorerId)?.name || event.scorerId
      const transfers = Object.entries(event.deltas)
        .map(([pid, delta]) => {
          const name = state.players.find((p) => p.id === pid)?.name || pid
          return `${name} ${delta >= 0 ? '+' : ''}${delta}`
        })
        .join('; ')
      return [event.at, event.kind, scorer, event.note || '', transfers]
    })
  ]
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(events), 'События')

  const buyInRows = [
    ['Время', 'Игрок', 'Тип', 'Сумма, ₽', 'Фишки', 'Тур', 'Заметка'],
    ...buyIns.map((item) => [
      item.at,
      state.players.find((p) => p.id === item.playerId)?.name || item.playerId,
      buyInKindLabel(item.kind),
      item.money,
      item.chips,
      item.roundNumber ?? '',
      item.note || ''
    ])
  ]
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(buyInRows), 'Взносы')

  const prizeRows = [
    ['Место', '%', 'Сумма, ₽'],
    ...splitPrizes(prizes, state.tournament.bank?.prizePlaces || []).map((row) => [
      row.place,
      row.percent,
      row.amount
    ])
  ]
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(prizeRows), 'Призовые')

  return wb
}

export const downloadKolkhozExcel = (state: KolkhozState, filename?: string) => {
  const wb = buildKolkhozWorkbook(state)
  const name = filename || `kolkhoz-${new Date().toISOString().slice(0, 10)}.xlsx`
  XLSX.writeFile(wb, name)
}
