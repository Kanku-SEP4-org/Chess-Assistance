import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, test, vi } from 'vitest'
import AngrinessPredictor from './AngrinessPredictor'

function renderAngrinessPredictor() {
  return render(
    <MemoryRouter>
      <AngrinessPredictor />
    </MemoryRouter>
  )
}

beforeEach(() => {
  localStorage.clear()
  localStorage.setItem('lichess_user', JSON.stringify({ player_username: 'TestUser' }))
  globalThis.fetch = vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
  )
})

describe('AngrinessPredictor — ML API flow', () => {
  test('posts game prediction to /predictions/angriness/lichess and renders result', async () => {
    globalThis.fetch = vi.fn((url) => {
      if (String(url).includes('/predictions/angriness/lichess')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            status: 'ok',
            game_id: 'abc12345',
            game_url: 'https://lichess.org/abc12345',
            player_side: 'white',
            player_rating: 1600,
            opponent_rating: 1550,
            opening: 'Sicilian Defense',
            time_control: '5+0',
            angriness: 4,
          }),
        })
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
    })

    renderAngrinessPredictor()

    fireEvent.change(screen.getByPlaceholderText(/game id/i), { target: { value: 'abc12345' } })
    fireEvent.change(screen.getByPlaceholderText(/player username/i), { target: { value: 'Magnus' } })
    fireEvent.click(screen.getByRole('button', { name: /^predict$/i }))

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/predictions/angriness/lichess'),
        expect.objectContaining({ method: 'POST' })
      )
    })
    expect(await screen.findByText('4/5')).toBeInTheDocument()
    expect(screen.getByText(/sicilian defense/i)).toBeInTheDocument()
  })

  test('loads recent games from /angriness/recent-games and predicts selected game', async () => {
    globalThis.fetch = vi.fn((url) => {
      const target = String(url)
      if (target.includes('/angriness/recent-games/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            games: [
              {
                game_id: 'game1234',
                opponent: 'Opponent',
                result: 'loss',
                opening: 'French Defense',
                time_control: '10+0',
                speed: 'rapid',
                has_analysis: true,
                consecutive_losses_before: 2,
              },
            ],
          }),
        })
      }
      if (target.includes('/predictions/angriness/lichess')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            status: 'ok',
            game_id: 'game1234',
            game_url: 'https://lichess.org/game1234',
            player_side: 'black',
            player_rating: 1500,
            opponent_rating: 1520,
            opening: 'French Defense',
            time_control: '10+0',
            angriness: 3,
          }),
        })
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
    })

    renderAngrinessPredictor()

    fireEvent.change(screen.getByPlaceholderText(/search by username/i), { target: { value: 'Magnus' } })
    fireEvent.click(screen.getByRole('button', { name: /^search$/i }))

    expect(await screen.findByText(/french defense/i)).toBeInTheDocument()
    const predictButtons = screen.getAllByRole('button', { name: /^predict$/i })
    fireEvent.click(predictButtons[predictButtons.length - 1])

    expect(await screen.findByText('3/5')).toBeInTheDocument()
  })

  test('shows FastAPI detail errors from prediction endpoint', async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ detail: 'Game has no analysis' }),
      })
    )

    renderAngrinessPredictor()

    fireEvent.change(screen.getByPlaceholderText(/game id/i), { target: { value: 'abc12345' } })
    fireEvent.change(screen.getByPlaceholderText(/player username/i), { target: { value: 'Magnus' } })
    fireEvent.click(screen.getByRole('button', { name: /^predict$/i }))

    expect(await screen.findByText(/game has no analysis/i)).toBeInTheDocument()
  })
})
