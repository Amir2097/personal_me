export type Locale = 'ru' | 'en'

const messages: Record<Locale, Record<string, string>> = {
  ru: {
    hub_label: 'хаб разработчика',
    hub_for_employers: 'работодателям',
    hub_for_users: 'пользователям',
    hub_for_guests: 'гостям',
    workspace: 'Рабочая область',
    hints: 'Подсказки',
    cd_home: 'cd ~',
    terminal_tab: 'терминал',
    projects_tab: 'проекты',
    logs_tab: 'логи',
    mobile_nav: 'меню'
  },
  en: {
    hub_label: 'developer hub',
    hub_for_employers: 'employers',
    hub_for_users: 'users',
    hub_for_guests: 'guests',
    workspace: 'Workspace',
    hints: 'Hints',
    cd_home: 'cd ~',
    terminal_tab: 'terminal',
    projects_tab: 'projects',
    logs_tab: 'logs',
    mobile_nav: 'menu'
  }
}

export function useLocale() {
  const locale = useState<Locale>('locale', () => 'ru')

  onMounted(() => {
    const saved = localStorage.getItem('terminal_locale') as Locale | null
    if (saved === 'ru' || saved === 'en') {
      locale.value = saved
    }
  })

  watch(locale, (value) => {
    if (import.meta.client) {
      localStorage.setItem('terminal_locale', value)
    }
  })

  const t = (key: string) => messages[locale.value][key] ?? key

  const setLocale = (value: Locale) => {
    locale.value = value
  }

  return { locale, t, setLocale }
}
