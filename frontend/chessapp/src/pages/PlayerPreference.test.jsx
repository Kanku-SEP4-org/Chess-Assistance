import { render, screen, fireEvent, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import PlayerPreference from './PlayerPreference'

function renderComponent() {
  return render(
    <MemoryRouter>
      <PlayerPreference />
    </MemoryRouter>
  )
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('PlayerPreference — display', () => {
  test('renders heading and description', () => {
    renderComponent()
    expect(screen.getByText(/player preferences/i)).toBeInTheDocument()
    expect(screen.getByText(/customize your chess session/i)).toBeInTheDocument()
  })

  test('renders all form inputs', () => {
    renderComponent()
    expect(screen.getByPlaceholderText(/enter player id/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/enter game limit/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/enter minutes/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/enter break interval/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/enter rest duration/i)).toBeInTheDocument()
  })

  test('renders Save Preferences button', () => {
    renderComponent()
    expect(screen.getByRole('button', { name: /save preferences/i })).toBeInTheDocument()
  })
})

describe('PlayerPreference — interaction', () => {
  test('updates input values on change', () => {
    renderComponent()

    const fields = [
      { placeholder: /enter player id/i, value: '42', name: 'player_id' },
      { placeholder: /enter game limit/i, value: '10', name: 'daily_game_limit' },
      { placeholder: /enter minutes/i, value: '120', name: 'daily_playtime_limit_min' },
      { placeholder: /enter break interval/i, value: '30', name: 'break_interval_min' },
      { placeholder: /enter rest duration/i, value: '15', name: 'recommend_rest_min' },
    ]

    for (const { placeholder, value, name } of fields) {
      const input = screen.getByPlaceholderText(placeholder)
      fireEvent.change(input, { target: { value, name } })
      expect(input.value).toBe(value)
    }
  })

  test('shows success message after submit and hides after timeout', () => {
    renderComponent()

    fireEvent.click(screen.getByRole('button', { name: /save preferences/i }))
    expect(screen.getByText(/preferences saved successfully/i)).toBeInTheDocument()

    act(() => { vi.advanceTimersByTime(3000) })
    expect(screen.queryByText(/preferences saved successfully/i)).not.toBeInTheDocument()
  })
})
