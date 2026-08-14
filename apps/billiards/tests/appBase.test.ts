import { describe, expect, it } from 'vitest'
import { joinAppPath, normalizeAppBase } from '../utils/appBase'

describe('app base path', () => {
  it('normalizes trailing slashes', () => {
    expect(normalizeAppBase('/')).toBe('/')
    expect(normalizeAppBase('/billiards')).toBe('/billiards/')
    expect(normalizeAppBase('/billiards/')).toBe('/billiards/')
  })

  it('joins routes for hub and standalone installs', () => {
    expect(joinAppPath('/billiards/', 'tv')).toBe('/billiards/tv')
    expect(joinAppPath('/', '/tv')).toBe('/tv')
    expect(joinAppPath('/', 'cup/tv')).toBe('/cup/tv')
  })
})
