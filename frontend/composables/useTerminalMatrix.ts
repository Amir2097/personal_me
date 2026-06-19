export function useTerminalMatrix() {
  const active = useState('terminal-matrix-active', () => false)

  const show = () => {
    active.value = true
  }

  const hide = () => {
    active.value = false
  }

  return { active, show, hide }
}
