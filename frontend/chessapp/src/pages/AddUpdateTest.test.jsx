import { render, screen, fireEvent } from "@testing-library/react";
import AddUpdateTest from "./AddUpdateTest";
import { addTest } from "../services/testService";

jest.mock("../services/testService");

describe("AddUpdateTest Component", () => {

  test("renders all form fields", () => {

    render(<AddUpdateTest />);

    expect(screen.getByText(/Add Test/i)).toBeInTheDocument();

    expect(screen.getByLabelText(/Test Name/i)).toBeInTheDocument();

    expect(screen.getByLabelText(/Description/i)).toBeInTheDocument();

    expect(screen.getByLabelText(/Duration/i)).toBeInTheDocument();

    expect(screen.getByLabelText(/Threshold/i)).toBeInTheDocument();

  });

  test("updates input values", () => {

    render(<AddUpdateTest />);

    const nameInput = screen.getByLabelText(/Test Name/i);

    fireEvent.change(nameInput, {
      target: { value: "Memory Test" }
    });

    expect(nameInput.value).toBe("Memory Test");

  });

  test("submits form successfully", async () => {

    addTest.mockResolvedValue({
      data: { success: true }
    });

    window.alert = jest.fn();

    render(<AddUpdateTest />);

    fireEvent.change(screen.getByLabelText(/Test Name/i), {
      target: { value: "Reaction Test" }
    });

    fireEvent.change(screen.getByLabelText(/Description/i), {
      target: { value: "Speed reaction test" }
    });

    fireEvent.change(screen.getByLabelText(/Duration/i), {
      target: { value: "30" }
    });

    fireEvent.change(screen.getByLabelText(/Threshold/i), {
      target: { value: "80" }
    });

    fireEvent.click(screen.getByText(/Save Test/i));

    expect(addTest).toHaveBeenCalled();

  });

  test("handles API failure", async () => {

    addTest.mockRejectedValue(new Error("API Error"));

    window.alert = jest.fn();

    render(<AddUpdateTest />);

    fireEvent.click(screen.getByText(/Save Test/i));

  });

});