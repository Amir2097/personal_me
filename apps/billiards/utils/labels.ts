import type { PlayerCategory, PlayerStatus } from '~/types/kolkhoz'

export const modeLabel = (mode: string | null) => {
  if (mode === 'casual') return 'Быстрый стол'
  if (mode === 'tournament') return 'Турнир'
  return '—'
}

export const tournamentKindLabel = (kind: string | undefined) => {
  if (kind === 'organizer') return 'организаторская'
  if (kind === 'detailed') return 'подробная игра'
  return kind || '—'
}

export const groupLabel = (category: PlayerCategory | number, short = false) => {
  const n = Number(category)
  return short ? `Гр. ${n}` : `Группа ${n}`
}

export const groupHint = (category: PlayerCategory | number) => {
  if (Number(category) === 1) return 'сильнее'
  if (Number(category) === 3) return 'слабее'
  return 'средняя'
}

export const statusLabel = (status: PlayerStatus) => {
  if (status === 'eliminated') return 'вне игры'
  return 'в игре'
}

/** Stable pastel palette for avatar backgrounds (works on light & dark). */
export const avatarColor = (seed: string) => {
  let hash = 0
  for (let i = 0; i < seed.length; i += 1) {
    hash = seed.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hues = [152, 168, 38, 18, 200, 280, 320]
  const hue = hues[Math.abs(hash) % hues.length]!
  return `hsl(${hue} 42% 38%)`
}

export const playerInitials = (name: string) => {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return '?'
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase()
  return `${parts[0]![0] || ''}${parts[1]![0] || ''}`.toUpperCase()
}
