import { render, screen, fireEvent, act, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import Home from './Home'

function renderHome() {
  return render(
    <MemoryRouter>
      <Home />
    </MemoryRouter>
  )
}

beforeEach(() => {
  localStorage.clear()
  vi.useFakeTimers()
  globalThis.fetch = vi.fn(() =>
    Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) })
  )
})

afterEach(() => {
  vi.useRealTimers()
})

describe('Home — hero section', () => {
  test('renders Chess Performance Assistant eyebrow', () => {
    renderHome()
    expect(screen.getByText(/chess performance assistant/i)).toBeInTheDocument()
  })

  test('renders Start Monitoring button', () => {
    renderHome()
    expect(screen.getByRole('button', { name: /start monitoring/i })).toBeInTheDocument()
  })

  test('hero text cycles on interval', () => {
    renderHome()
    const firstActive = document.querySelectorAll('.hero-line.active')
    expect(firstActive.length).toBeGreaterThan(0)

    act(() => { vi.advanceTimersByTime(3000) })

    const afterCycle = document.querySelectorAll('.hero-line.active')
    expect(afterCycle.length).toBeGreaterThan(0)
  })
})

describe('Home — monitoring dashboard', () => {
  test('dashboard is hidden before Start Monitoring is clicked', () => {
    renderHome()
    expect(screen.queryByText(/live metrics/i)).not.toBeInTheDocument()
  })

  test('clicking Start Monitoring reveals the dashboard', () => {
    renderHome()
    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    expect(screen.getByText(/live metrics/i)).toBeInTheDocument()
  })

  test('dashboard shows metric cards after monitoring starts', () => {
    renderHome()
    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    expect(screen.getByText(/temperature/i)).toBeInTheDocument()
    expect(screen.getByText(/co2 level/i)).toBeInTheDocument()
    expect(screen.getByText(/light level/i)).toBeInTheDocument()
    expect(screen.getByText(/focus score/i)).toBeInTheDocument()
  })

  test('shows login prompt when no user is logged in', () => {
    renderHome()
    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    expect(screen.getByText(/log in with lichess/i)).toBeInTheDocument()
  })

  test('shows Start Chess Session button when user is logged in', () => {
    localStorage.setItem('lichess_user', JSON.stringify({ player_id: 1, player_username: 'Magnus' }))
    renderHome()
    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    expect(screen.getByRole('button', { name: /start chess session/i })).toBeInTheDocument()
  })

  test('clicking Start Chess Session shows the session form', () => {
    localStorage.setItem('lichess_user', JSON.stringify({ player_id: 1, player_username: 'Magnus' }))
    renderHome()
    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    fireEvent.click(screen.getByRole('button', { name: /start chess session/i }))
    expect(screen.getByText(/time you went to sleep/i)).toBeInTheDocument()
    expect(screen.getByText(/water intake so far/i)).toBeInTheDocument()
  })
})

describe('Home — session form', () => {
  function openSessionForm() {
    localStorage.setItem('lichess_user', JSON.stringify({ player_id: 1, player_username: 'Magnus' }))
    renderHome()
    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    fireEvent.click(screen.getByRole('button', { name: /start chess session/i }))
  }

  test('Start Session button does nothing when time inputs are empty', async () => {
    openSessionForm()
    fireEvent.click(screen.getByRole('button', { name: /^start session$/i }))
    expect(globalThis.fetch).not.toHaveBeenCalledWith(
      expect.stringContaining('/session/evaluate'),
      expect.anything()
    )
  })

  test('submitting form calls /session/evaluate', async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          alerts: [{ level: 'yellow', message: 'Test alert' }],
          sleep_duration: '6h 0m',
          awake_duration: '2h 0m',
        }),
      })
    )

    openSessionForm()
    const [sleepInput, wakeInput] = document.querySelectorAll('input[type="time"]')
    fireEvent.change(sleepInput, { target: { value: '23:00' } })
    fireEvent.change(wakeInput, { target: { value: '05:00' } })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^start session$/i }))
    })

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/session/evaluate'),
      expect.objectContaining({ method: 'POST' })
    )
  })
})
