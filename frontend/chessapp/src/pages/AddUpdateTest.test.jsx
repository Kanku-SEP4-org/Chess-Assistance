import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AddUpdateTest from "./AddUpdateTest";
import * as testService from "../services/testService";

jest.mock("../services/testService");

describe("AddUpdateTest Component", () => {

  test("renders Add Test heading", () => {

    render(<AddUpdateTest />);

    expect(
      screen.getByText(/Add Test/i)
    ).toBeInTheDocument();

  });

  test("renders all input fields", () => {

    render(<AddUpdateTest />);

    const inputs = screen.getAllByRole("textbox");

    expect(inputs.length).toBe(2);

  });

  test("updates test name input", () => {

    render(<AddUpdateTest />);

    const textInputs =
      screen.getAllByRole("textbox");

    const testNameInput = textInputs[0];

    fireEvent.change(testNameInput, {
      target: {
        value: "Sleep Test"
      }
    });

    expect(testNameInput.value).toBe("Sleep Test");

  });

  test("renders number inputs", () => {

    render(<AddUpdateTest />);

    const numberInputs =
      screen.getAllByRole("spinbutton");

    expect(numberInputs.length).toBe(2);

  });

  test("renders save button", () => {

    render(<AddUpdateTest />);

    expect(
      screen.getByRole("button", {
        name: /Save Test/i
      })
    ).toBeInTheDocument();

  });

  test("submits form successfully", async () => {

    testService.addTest.mockResolvedValue({
      data: { success: true }
    });

    window.alert = jest.fn();

    render(<AddUpdateTest />);

    const textInputs =
      screen.getAllByRole("textbox");

    const numberInputs =
      screen.getAllByRole("spinbutton");

    fireEvent.change(textInputs[0], {
      target: { value: "Sleep Test" }
    });

    fireEvent.change(textInputs[1], {
      target: { value: "Description" }
    });

    fireEvent.change(numberInputs[0], {
      target: { value: "30" }
    });

    fireEvent.change(numberInputs[1], {
      target: { value: "80" }
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: /Save Test/i
      })
    );

    await waitFor(() => {

      expect(testService.addTest)
        .toHaveBeenCalled();

      expect(window.alert)
        .toHaveBeenCalledWith(
          "Test Added Successfully"
        );

    });

  });

});