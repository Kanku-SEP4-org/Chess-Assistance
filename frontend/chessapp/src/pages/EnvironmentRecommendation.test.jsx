import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, test, vi } from 'vitest'
import EnvironmentRecommendation from './EnvironmentRecommendation'

function renderEnvironmentRecommendation() {
  return render(
    <MemoryRouter>
      <EnvironmentRecommendation />
    </MemoryRouter>
  )
}

beforeEach(() => {
  localStorage.clear()
  globalThis.fetch = vi.fn((url) => {
    const target = String(url)
    if (target.includes('/iot/temp')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ value: 21 }) })
    }
    if (target.includes('/iot/light')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ value: 1500 }) })
    }
    if (target.includes('/iot/co2')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ value: 700 }) })
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
  })
})

describe('EnvironmentRecommendation — ML API flow', () => {
  test('posts recommendation inputs to /recommendations/environment and renders result', async () => {
    globalThis.fetch = vi.fn((url) => {
      const target = String(url)
      if (target.includes('/iot/temp')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ value: 21 }) })
      }
      if (target.includes('/iot/light')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ value: 1500 }) })
      }
      if (target.includes('/iot/co2')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ value: 700 }) })
      }
      if (target.includes('/recommendations/environment')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            current_win_probability: 0.42,
            recommended_factor: 'co2',
            current_value: 700,
            recommended_value: 500,
            improved_win_probability: 0.49,
            increase: 0.07,
            increase_percentage_points: 7,
            message: 'Lowering CO2 may increase your win probability.',
            all_candidates: [
              {
                factor: 'co2',
                current_value: 700,
                recommended_value: 500,
                win_probability: 0.49,
                increase_percentage_points: 7,
              },
            ],
          }),
        })
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
    })

    renderEnvironmentRecommendation()

    fireEvent.click(screen.getByRole('button', { name: /get recommendation/i }))

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/recommendations/environment'),
        expect.objectContaining({ method: 'POST' })
      )
    })
    expect(await screen.findByText(/recommended action/i)).toBeInTheDocument()
    expect(screen.getAllByText(/co2/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/lowering co2/i)).toBeInTheDocument()
  })

  test('shows FastAPI detail errors from recommendation endpoint', async () => {
    globalThis.fetch = vi.fn((url) => {
      const target = String(url)
      if (target.includes('/recommendations/environment')) {
        return Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ detail: 'Model unavailable' }),
        })
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ value: 1 }) })
    })

    renderEnvironmentRecommendation()
    fireEvent.click(screen.getByRole('button', { name: /get recommendation/i }))

    expect(await screen.findByText(/model unavailable/i)).toBeInTheDocument()
  })
})
