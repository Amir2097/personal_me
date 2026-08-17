import { test } from '@playwright/test'

/**
 * Full sync flow — run locally with stack up:
 *   docker compose -f docker-compose.billiards.yml up --build
 *   cd apps/billiards && NUXT_PUBLIC_API_BASE_URL=http://localhost:8010 npm run dev
 *
 *   npx playwright test e2e/sync-room.spec.ts
 */
test.describe.configure({ mode: 'serial' })

test.describe('operator sync room @integration', () => {
  test.skip(
    !process.env.E2E_API_URL,
    'Set E2E_API_URL=http://localhost:8010 to run integration sync tests'
  )

  test('operator creates room and guest reads session', async ({ request }) => {
    const api = process.env.E2E_API_URL!.replace(/\/$/, '')

    const login = await request.post(`${api}/api/v1/billiards/auth/login`, {
      data: { username: 'admin', password: 'admin123' }
    })
    test.skip(login.status() !== 200, 'Admin login failed — is the API running?')
    const { access_token: token } = await login.json()
    const headers = { Authorization: `Bearer ${token}` }

    const created = await request.post(`${api}/api/v1/kolkhoz/sessions`, { headers })
    expect(created.ok()).toBeTruthy()
    const { code } = await created.json()

    const guest = await request.get(`${api}/api/v1/kolkhoz/sessions/${code}`)
    expect(guest.ok()).toBeTruthy()
    expect((await guest.json()).code).toBe(code)
  })
})
