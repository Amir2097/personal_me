export type SessionLogEntry = {
  ts: string
  level: 'info' | 'warn' | 'cmd' | 'auth'
  message: string
}

export function useTerminalLogs() {
  const logs = useState<SessionLogEntry[]>('terminal-session-logs', () => [])

  const pushLog = (level: SessionLogEntry['level'], message: string) => {
    logs.value.push({
      ts: new Date().toLocaleTimeString('ru-RU'),
      level,
      message
    })
    if (logs.value.length > 200) {
      logs.value = logs.value.slice(-200)
    }
  }

  const clearLogs = () => {
    logs.value = []
  }

  return { logs, pushLog, clearLogs }
}
