import { render, screen, fireEvent, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, test, vi } from 'vitest'
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

  test('sleep form is hidden until toggle button is clicked', () => {
    renderHome()
    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    expect(screen.queryByRole('heading', { name: /sleep tracker/i })).not.toBeInTheDocument()
  })

  test('clicking sleep toggle shows Sleep Tracker form', () => {
    renderHome()
    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    fireEvent.click(screen.getByRole('button', { name: /how much time did i sleep/i }))
    expect(screen.getByRole('heading', { name: /sleep tracker/i })).toBeInTheDocument()
  })

  test('clicking sleep toggle again hides the form', () => {
    renderHome()
    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    const toggleBtn = screen.getByRole('button', { name: /how much time did i sleep/i })
    fireEvent.click(toggleBtn)
    fireEvent.click(toggleBtn)
    expect(screen.queryByRole('heading', { name: /sleep tracker/i })).not.toBeInTheDocument()
  })
})

describe('Home — sleep calculator', () => {
  function openSleepForm() {
    renderHome()
    fireEvent.click(screen.getByRole('button', { name: /start monitoring/i }))
    fireEvent.click(screen.getByRole('button', { name: /how much time did i sleep/i }))
  }

  test('Calculate Sleep button does nothing when inputs are empty', () => {
    openSleepForm()
    fireEvent.click(screen.getByRole('button', { name: /calculate sleep/i }))
    expect(screen.queryByText(/you slept for/i)).not.toBeInTheDocument()
  })

  test('calculates overnight sleep via 22:00 to 06:00', () => {
    openSleepForm()
    const [sleepInput, wakeInput] = document.querySelectorAll('input[type="time"]')
    fireEvent.change(sleepInput, { target: { value: '22:00' } })
    fireEvent.change(wakeInput, { target: { value: '06:00' } })
    fireEvent.click(screen.getByRole('button', { name: /calculate sleep/i }))
    expect(screen.getByText(/you slept for/i)).toBeInTheDocument()
    expect(screen.getByText(/8h 0m/i)).toBeInTheDocument()
  })

  test('calculates 7h 45m for 23:30 to 07:15', () => {
    openSleepForm()
    const inputs = document.querySelectorAll('input[type="time"]')
    fireEvent.change(inputs[0], { target: { value: '23:30' } })
    fireEvent.change(inputs[1], { target: { value: '07:15' } })
    fireEvent.click(screen.getByRole('button', { name: /calculate sleep/i }))
    expect(screen.getByText(/7h 45m/i)).toBeInTheDocument()
  })

  test('calculates 24h when sleep and wake time are identical', () => {
    openSleepForm()
    const inputs = document.querySelectorAll('input[type="time"]')
    fireEvent.change(inputs[0], { target: { value: '08:00' } })
    fireEvent.change(inputs[1], { target: { value: '08:00' } })
    fireEvent.click(screen.getByRole('button', { name: /calculate sleep/i }))
    expect(screen.getByText(/24h 0m/i)).toBeInTheDocument()
  })
})
