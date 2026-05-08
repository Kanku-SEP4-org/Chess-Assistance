import { render, screen } from '@testing-library/react';
import App from './App';

test('renders win predictor heading', () => {
  render(<App />);
  const heading = screen.getByText(/chess win predictor/i);
  expect(heading).toBeInTheDocument();
});
