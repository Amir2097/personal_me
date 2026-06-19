export function useTerminalAliases() {
  const aliases = useState<Record<string, string>>('terminal-aliases', () => ({}))

  const load = () => {
    if (!import.meta.client) return
    try {
      const raw = localStorage.getItem('terminal_aliases')
      if (raw) {
        aliases.value = JSON.parse(raw) as Record<string, string>
      }
    } catch {
      aliases.value = {}
    }
  }

  const save = () => {
    if (import.meta.client) {
      localStorage.setItem('terminal_aliases', JSON.stringify(aliases.value))
    }
  }

  onMounted(load)

  const resolveAlias = (command: string): string => {
    const trimmed = command.trim()
    const space = trimmed.indexOf(' ')
    const head = space === -1 ? trimmed : trimmed.slice(0, space)
    const tail = space === -1 ? '' : trimmed.slice(space)
    const mapped = aliases.value[head.toLowerCase()]
    if (!mapped) {
      return command
    }
    return `${mapped}${tail}`
  }

  const setAlias = (name: string, value: string) => {
    aliases.value = { ...aliases.value, [name.toLowerCase()]: value }
    save()
  }

  const removeAlias = (name: string) => {
    const next = { ...aliases.value }
    delete next[name.toLowerCase()]
    aliases.value = next
    save()
  }

  const listAliases = () =>
    Object.entries(aliases.value).map(([name, value]) => `${name}=${value}`)

  return { aliases, resolveAlias, setAlias, removeAlias, listAliases }
}
