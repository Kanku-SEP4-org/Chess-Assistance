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
  globalThis.fetch = vi.fn(() =>
    Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) })
  )
  globalThis.alert = vi.fn()
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
    vi.useFakeTimers()
    renderHome()
    const firstActive = document.querySelectorAll('.hero-line.active')
    expect(firstActive.length).toBeGreaterThan(0)

    act(() => { vi.advanceTimersByTime(3000) })

    const afterCycle = document.querySelectorAll('.hero-line.active')
    expect(afterCycle.length).toBeGreaterThan(0)
    vi.useRealTimers()
  })
})

describe('Home — auth check on mount', () => {
  test('clears user when /auth/me returns not ok', async () => {
    localStorage.setItem('lichess_user', JSON.stringify({ player_id: 1, player_username: 'Magnus' }))
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({ ok: false, status: 401, json: () => Promise.resolve({}) })
    )

    await act(async () => { renderHome() })

    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    expect(screen.getByText(/log in with lichess/i)).toBeInTheDocument()
    expect(localStorage.getItem('lichess_user')).toBeNull()
  })

  test('keeps user when /auth/me fetch throws', async () => {
    localStorage.setItem('lichess_user', JSON.stringify({ player_id: 1, player_username: 'Magnus' }))
    globalThis.fetch = vi.fn(() => Promise.reject(new Error('network')))

    await act(async () => { renderHome() })

    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    expect(screen.getByRole('button', { name: /start chess session/i })).toBeInTheDocument()
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
    expect(screen.getByText(/water drank/i)).toBeInTheDocument()
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

  test('evaluate error shows alert to user', async () => {
    globalThis.fetch = vi.fn(() => Promise.reject(new Error('network')))

    openSessionForm()
    const [sleepInput, wakeInput] = document.querySelectorAll('input[type="time"]')
    fireEvent.change(sleepInput, { target: { value: '23:00' } })
    fireEvent.change(wakeInput, { target: { value: '05:00' } })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^start session$/i }))
    })

    expect(globalThis.alert).toHaveBeenCalledWith('Failed to evaluate readiness')
  })

  test('water intake input accepts changes', () => {
    openSessionForm()
    const waterInput = screen.getByPlaceholderText(/e\.g\. 500/i)
    fireEvent.change(waterInput, { target: { value: '750' } })
    expect(waterInput.value).toBe('750')
  })
})

describe('Home — alerts display', () => {
  async function showAlertsWithWarnings() {
    localStorage.setItem('lichess_user', JSON.stringify({ player_id: 1, player_username: 'Magnus' }))

    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true, status: 200,
        json: () => Promise.resolve({
          alerts: [
            { level: 'yellow', message: 'Low sleep detected' },
            { level: 'red', message: 'Very tired' },
          ],
          sleep_duration: '5h 30m',
          awake_duration: '2h 0m',
        }),
      })
    )

    renderHome()
    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    fireEvent.click(screen.getByRole('button', { name: /start chess session/i }))

    const [sleepInput, wakeInput] = document.querySelectorAll('input[type="time"]')
    fireEvent.change(sleepInput, { target: { value: '01:00' } })
    fireEvent.change(wakeInput, { target: { value: '06:30' } })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^start session$/i }))
    })
  }

  test('shows alerts and durations after evaluate', async () => {
    await showAlertsWithWarnings()

    expect(screen.getByText(/low sleep detected/i)).toBeInTheDocument()
    expect(screen.getByText(/very tired/i)).toBeInTheDocument()
    expect(screen.getByText(/5h 30m/)).toBeInTheDocument()
    expect(screen.getByText(/2h 0m/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /start anyway/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
  })

  test('Cancel clears alerts and shows form again', async () => {
    await showAlertsWithWarnings()

    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))

    expect(screen.queryByText(/low sleep detected/i)).not.toBeInTheDocument()
    expect(screen.getByText(/time you went to sleep/i)).toBeInTheDocument()
  })

  test('no alerts shows prediction before confirming session start', async () => {
    localStorage.setItem('lichess_user', JSON.stringify({ player_id: 1, player_username: 'Magnus' }))

    globalThis.fetch = vi.fn((url) => {
      const target = String(url)
      if (target.includes('/iot/temp')) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ value: 21 }) })
      }
      if (target.includes('/iot/light')) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ value: 1500 }) })
      }
      if (target.includes('/iot/co2')) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ value: 700 }) })
      }
      if (target.includes('/session/evaluate')) {
        return Promise.resolve({
          ok: true, status: 200,
          json: () => Promise.resolve({
            alerts: [],
            sleep_duration: '8h 0m',
            awake_duration: '1h 0m',
          }),
        })
      }
      if (target.includes('/predict')) {
        return Promise.resolve({
          ok: true, status: 200,
          json: () => Promise.resolve({ prediction: 0.62 }),
        })
      }
      if (target.includes('/session/start')) {
        return Promise.resolve({
          ok: true, status: 200,
          json: () => Promise.resolve({ success: true, session_id: 42 }),
        })
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) })
    })

    renderHome()
    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    await waitFor(() => {
      expect(screen.getByText(/21\.0/)).toBeInTheDocument()
    })
    fireEvent.click(screen.getByRole('button', { name: /start chess session/i }))

    const [sleepInput, wakeInput] = document.querySelectorAll('input[type="time"]')
    fireEvent.change(sleepInput, { target: { value: '22:00' } })
    fireEvent.change(wakeInput, { target: { value: '06:00' } })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^start session$/i }))
    })

    await waitFor(() => {
      expect(screen.getByText(/predicted win chance: 62%/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/all good/i)).toBeInTheDocument()

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^start session$/i }))
    })

    await waitFor(() => {
      expect(screen.getByText(/session #42 is active/i)).toBeInTheDocument()
    })
  })
})

describe('Home — session lifecycle', () => {
  async function startActiveSession() {
    localStorage.setItem('lichess_user', JSON.stringify({ player_id: 1, player_username: 'Magnus' }))

    globalThis.fetch = vi.fn((url) => {
      const target = String(url)
      if (target.includes('/iot/temp')) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ value: 21 }) })
      }
      if (target.includes('/iot/light')) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ value: 1500 }) })
      }
      if (target.includes('/iot/co2')) {
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ value: 700 }) })
      }
      if (target.includes('/session/evaluate')) {
        return Promise.resolve({
          ok: true, status: 200,
          json: () => Promise.resolve({
            alerts: [{ level: 'yellow', message: 'warning' }],
            sleep_duration: '6h', awake_duration: '2h',
          }),
        })
      }
      if (target.includes('/predict')) {
        return Promise.resolve({
          ok: true, status: 200,
          json: () => Promise.resolve({ prediction: 0.55 }),
        })
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) })
    })

    renderHome()
    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    fireEvent.click(screen.getByRole('button', { name: /start chess session/i }))

    const [sleepInput, wakeInput] = document.querySelectorAll('input[type="time"]')
    fireEvent.change(sleepInput, { target: { value: '23:00' } })
    fireEvent.change(wakeInput, { target: { value: '05:00' } })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /^start session$/i }))
    })

    return screen.findByRole('button', { name: /start anyway/i })
  }

  test('Start Anyway calls /session/start and shows active session', async () => {
    const startAnywayBtn = await startActiveSession()

    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true, status: 200,
        json: () => Promise.resolve({ success: true, session_id: 7 }),
      })
    )

    await act(async () => { fireEvent.click(startAnywayBtn) })

    await waitFor(() => {
      expect(screen.getByText(/session #7 is active/i)).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument()
  })

  test('startSession handles 401 by logging out', async () => {
    const startAnywayBtn = await startActiveSession()

    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false, status: 401,
        json: () => Promise.resolve({}),
      })
    )

    await act(async () => { fireEvent.click(startAnywayBtn) })

    expect(globalThis.alert).toHaveBeenCalledWith(
      expect.stringContaining('session expired')
    )
    expect(localStorage.getItem('lichess_user')).toBeNull()
  })

  test('startSession handles non-success response', async () => {
    const startAnywayBtn = await startActiveSession()

    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true, status: 200,
        json: () => Promise.resolve({ success: false, message: 'already active' }),
      })
    )

    await act(async () => { fireEvent.click(startAnywayBtn) })

    expect(globalThis.alert).toHaveBeenCalledWith('already active')
  })

  test('startSession handles network error', async () => {
    const startAnywayBtn = await startActiveSession()

    globalThis.fetch = vi.fn(() => Promise.reject(new Error('offline')))

    await act(async () => { fireEvent.click(startAnywayBtn) })

    expect(globalThis.alert).toHaveBeenCalledWith('Failed to connect to server')
  })

  test('End Session ends successfully', async () => {
    const startAnywayBtn = await startActiveSession()

    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true, status: 200,
        json: () => Promise.resolve({ success: true, session_id: 10 }),
      })
    )
    await act(async () => { fireEvent.click(startAnywayBtn) })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument()
    })

    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true, status: 200,
        json: () => Promise.resolve({ success: true }),
      })
    )
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /end session/i }))
    })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start monitoring/i })).toBeInTheDocument()
    })
  })

  test('End Session handles failure response', async () => {
    const startAnywayBtn = await startActiveSession()

    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true, status: 200,
        json: () => Promise.resolve({ success: true, session_id: 10 }),
      })
    )
    await act(async () => { fireEvent.click(startAnywayBtn) })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument()
    })

    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true, status: 200,
        json: () => Promise.resolve({ success: false, message: 'server error' }),
      })
    )
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /end session/i }))
    })

    expect(globalThis.alert).toHaveBeenCalledWith('server error')
  })

  test('End Session handles network error', async () => {
    const startAnywayBtn = await startActiveSession()

    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true, status: 200,
        json: () => Promise.resolve({ success: true, session_id: 10 }),
      })
    )
    await act(async () => { fireEvent.click(startAnywayBtn) })

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument()
    })

    globalThis.fetch = vi.fn(() => Promise.reject(new Error('offline')))
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /end session/i }))
    })

    expect(globalThis.alert).toHaveBeenCalledWith('Failed to connect to server')
  })
})
