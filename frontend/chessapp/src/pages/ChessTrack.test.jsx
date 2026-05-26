import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, test, vi } from 'vitest'
import ChessTrack from './ChessTrack'

function renderChessTrack() {
  return render(
    <MemoryRouter>
      <ChessTrack />
    </MemoryRouter>
  )
}

beforeEach(() => {
  localStorage.clear()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('ChessTrack — display', () => {
  test('renders Chess.com player lookup heading', () => {
    renderChessTrack()
    expect(screen.getByText(/chess\.com player lookup/i)).toBeInTheDocument()
  })

  test('renders Lichess player lookup section', () => {
    renderChessTrack()
    expect(screen.getByText(/lichess player lookup/i)).toBeInTheDocument()
  })

  test('renders both search forms with inputs', () => {
    renderChessTrack()
    const inputs = screen.getAllByRole('textbox')
    expect(inputs.length).toBeGreaterThanOrEqual(3)
  })

  test('renders game history performance section', () => {
    renderChessTrack()
    expect(screen.getByText(/game history performance/i)).toBeInTheDocument()
  })
})

describe('ChessTrack — Chess.com search', () => {
  test('shows error when submitting empty Chess.com username', async () => {
    renderChessTrack()
    const [chessForm] = document.querySelectorAll('form')
    fireEvent.submit(chessForm)
    expect(await screen.findByText(/please enter a chess\.com username/i)).toBeInTheDocument()
  })

  test('shows loading state then displays stats on successful fetch', async () => {
    const mockData = {
      chess_rapid: { last: { rating: 1500 }, record: { win: 10, loss: 5, draw: 2 } },
      chess_blitz: { last: { rating: 1400 }, record: { win: 8, loss: 4, draw: 1 } },
      chess_bullet: { last: { rating: 1300 }, record: { win: 6, loss: 3, draw: 0 } },
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockData,
    }))

    renderChessTrack()
    const input = screen.getAllByRole('textbox')[0]
    fireEvent.change(input, { target: { value: 'hikaru' } })
    const [chessForm] = document.querySelectorAll('form')
    fireEvent.submit(chessForm)

    await waitFor(() => {
      expect(screen.getByText(/hikaru stats/i)).toBeInTheDocument()
    })
    expect(screen.getAllByText('1500').length).toBeGreaterThanOrEqual(1)
  })

  test('shows error on failed Chess.com fetch', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({}),
    }))

    renderChessTrack()
    const input = screen.getAllByRole('textbox')[0]
    fireEvent.change(input, { target: { value: 'nobody' } })
    const [chessForm] = document.querySelectorAll('form')
    fireEvent.submit(chessForm)

    expect(await screen.findByText(/could not find this chess\.com player/i)).toBeInTheDocument()
  })
})

describe('ChessTrack — Lichess search', () => {
  test('shows error when submitting empty Lichess username', async () => {
    renderChessTrack()
    const forms = document.querySelectorAll('form')
    fireEvent.submit(forms[1])
    expect(await screen.findByText(/please enter a lichess username/i)).toBeInTheDocument()
  })

  test('shows error on failed Lichess fetch', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({}),
    }))

    renderChessTrack()
    const inputs = screen.getAllByRole('textbox')
    fireEvent.change(inputs[1], { target: { value: 'nobody' } })
    const forms = document.querySelectorAll('form')
    fireEvent.submit(forms[1])

    expect(await screen.findByText(/could not find this lichess player/i)).toBeInTheDocument()
  })

  test('displays Lichess stats on successful fetch', async () => {
    const mockData = {
      username: 'drnykterstein',
      perfs: {
        rapid: { rating: 2800, games: 100 },
        blitz: { rating: 3000, games: 200 },
        bullet: { rating: 3200, games: 300 },
        classical: { rating: 2700, games: 50 },
      },
      patron: true,
      online: false,
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockData,
    }))

    renderChessTrack()
    const inputs = screen.getAllByRole('textbox')
    fireEvent.change(inputs[1], { target: { value: 'drnykterstein' } })
    const forms = document.querySelectorAll('form')
    fireEvent.submit(forms[1])

    await waitFor(() => {
      expect(screen.getByText(/drnykterstein stats/i)).toBeInTheDocument()
    })
    expect(screen.getByText('2800')).toBeInTheDocument()
  })

  test('displays N/A for missing Lichess perf categories', async () => {
    const mockData = {
      username: 'newbie',
      perfs: {},
      patron: false,
      online: true,
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockData,
    }))

    renderChessTrack()
    const inputs = screen.getAllByRole('textbox')
    fireEvent.change(inputs[1], { target: { value: 'newbie' } })
    const forms = document.querySelectorAll('form')
    fireEvent.submit(forms[1])

    await waitFor(() => {
      expect(screen.getByText(/newbie stats/i)).toBeInTheDocument()
    })
    const naElements = screen.getAllByText('N/A')
    expect(naElements.length).toBeGreaterThanOrEqual(4)
    expect(screen.getByText('Yes')).toBeInTheDocument()
  })
})

describe('ChessTrack — game history performance', () => {
  test('loads recent games and shows predict buttons for analyzed games', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        games: [
          {
            game_id: 'abc12345',
            opponent: 'Opponent',
            result: 'win',
            opening: 'Sicilian Defense',
            time_control: '5+0',
            speed: 'blitz',
            has_analysis: true,
          },
          {
            game_id: 'def67890',
            opponent: 'Other',
            result: 'loss',
            opening: 'French Defense',
            time_control: '10+0',
            speed: 'rapid',
            has_analysis: false,
          },
        ],
      }),
    }))

    renderChessTrack()
    const inputs = screen.getAllByRole('textbox')
    fireEvent.change(inputs[2], { target: { value: 'drnykterstein' } })
    const forms = document.querySelectorAll('form')
    fireEvent.submit(forms[2])

    await waitFor(() => {
      expect(screen.getByText(/sicilian defense/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/request analysis/i)).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: /predict/i })).toHaveLength(2)
  })

  test('predicts performance and displays verdict', async () => {
    vi.stubGlobal('fetch', vi.fn((url) => {
      if (String(url).includes('/accuracy/recent-games/')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            games: [
              {
                game_id: 'abc12345',
                opponent: 'Opponent',
                result: 'win',
                opening: 'Sicilian Defense',
                time_control: '5+0',
                speed: 'blitz',
                has_analysis: true,
              },
            ],
          }),
        })
      }

      return Promise.resolve({
        ok: true,
        json: async () => ({
          status: 'ok',
          game_id: 'abc12345',
          actual_centipawn_loss: 28,
          predicted_centipawn_loss: 42,
          verdict: 'overperformed',
        }),
      })
    }))

    renderChessTrack()
    const inputs = screen.getAllByRole('textbox')
    fireEvent.change(inputs[2], { target: { value: 'drnykterstein' } })
    const forms = document.querySelectorAll('form')
    fireEvent.submit(forms[2])

    await waitFor(() => {
      expect(screen.getByText(/sicilian defense/i)).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /predict/i }))

    await waitFor(() => {
      expect(screen.getByText(/overperformed/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/actual cpl/i)).toBeInTheDocument()
    expect(screen.getByText(/predicted cpl/i)).toBeInTheDocument()
  })
})
