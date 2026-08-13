/** Make tournament titles unique among already used names (case-insensitive). */
export const normalizeCupTitle = (name: string) => name.trim().replace(/\s+/g, ' ')

export const uniqueCupName = (desired: string, taken: string[]): string => {
  const base = normalizeCupTitle(desired) || 'Турнир'
  const used = new Set(taken.map((item) => normalizeCupTitle(item).toLowerCase()).filter(Boolean))
  if (!used.has(base.toLowerCase())) return base
  let index = 2
  while (used.has(`${base} ${index}`.toLowerCase())) index += 1
  return `${base} ${index}`
}
