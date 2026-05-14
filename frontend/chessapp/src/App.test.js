import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders Start Monitoring button", () => {

  render(<App />);

  const buttonElement = screen.getByText(/Start Monitoring/i);

  expect(buttonElement).toBeInTheDocument();

});