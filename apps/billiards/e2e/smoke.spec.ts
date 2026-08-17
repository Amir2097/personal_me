import { expect, test } from '@playwright/test'

test.describe('public pages smoke', () => {
  test('home loads', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('body')).toContainText('Сукно')
  })

  test('kolkhoz tv join form', async ({ page }) => {
    await page.goto('/tv')
    await expect(page.getByText('Код комнаты', { exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Подключить' })).toBeVisible()
  })

  test('login page', async ({ page }) => {
    await page.goto('/auth/login')
    await expect(page.getByRole('heading', { name: 'Вход' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Войти', exact: true })).toBeVisible()
  })

  test('cup bracket route', async ({ page }) => {
    test.setTimeout(60000)
    await page.goto('/cup', { waitUntil: 'domcontentloaded' })
    await expect(page.locator('body')).toContainText(/турнир|кубок/i)
  })
})
