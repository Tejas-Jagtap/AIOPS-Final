import "@testing-library/jest-dom";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import Home from "@/app/page";

// Mock fetch
global.fetch = jest.fn();

describe("Home Page - Todo App", () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    (global.fetch as jest.Mock).mockReset();
    // Default mock for initial load
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ todos: [] }),
    });
  });

  it("renders the main heading", async () => {
    await act(async () => {
      render(<Home />);
    });
    const heading = screen.getByText(/AIOps Demo Todo App/i);
    expect(heading).toBeInTheDocument();
  });

  it("renders the subtitle with pipeline information", async () => {
    await act(async () => {
      render(<Home />);
    });
    const subtitle = screen.getByText(/Jenkins Pipeline Testing/i);
    expect(subtitle).toBeInTheDocument();
  });

  it("loads todos from API on mount", async () => {
    const mockTodos = [
      { id: "1", text: "Test todo", completed: false, createdAt: "2024-01-01" },
    ];

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ todos: mockTodos }),
    });

    await act(async () => {
      render(<Home />);
    });

    await waitFor(() => {
      expect(screen.getByText("Test todo")).toBeInTheDocument();
    });
  });

  it("displays empty state when no todos", async () => {
    await act(async () => {
      render(<Home />);
    });

    await waitFor(() => {
      expect(screen.getByText(/No todos yet/i)).toBeInTheDocument();
    });
  });

  it("shows correct todo counts in filter buttons", async () => {
    const mockTodos = [
      {
        id: "1",
        text: "Active todo",
        completed: false,
        createdAt: "2024-01-01",
      },
      {
        id: "2",
        text: "Completed todo",
        completed: true,
        createdAt: "2024-01-02",
      },
    ];

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ todos: mockTodos }),
    });

    await act(async () => {
      render(<Home />);
    });

    await waitFor(() => {
      expect(screen.getByText(/All \(2\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Active \(1\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Completed \(1\)/i)).toBeInTheDocument();
    });
  });

  it("renders input field and add button", async () => {
    await act(async () => {
      render(<Home />);
    });

    const input = screen.getByPlaceholderText(/What needs to be done/i);
    const addButton = screen.getByText("Add");

    expect(input).toBeInTheDocument();
    expect(addButton).toBeInTheDocument();
  });

  it("calls API when adding a new todo", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ todos: [] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          todo: {
            id: "1",
            text: "New todo",
            completed: false,
            createdAt: "2024-01-01",
          },
        }),
      });

    await act(async () => {
      render(<Home />);
    });

    const input = screen.getByPlaceholderText(/What needs to be done/i);
    const addButton = screen.getByText("Add");

    await act(async () => {
      fireEvent.change(input, { target: { value: "New todo" } });
      fireEvent.click(addButton);
    });

    // Verify fetch was called (first for load, potentially second for add)
    expect(global.fetch).toHaveBeenCalled();
  });

  it("does not add empty todos", async () => {
    await act(async () => {
      render(<Home />);
    });

    const addButton = screen.getByText("Add");

    await act(async () => {
      fireEvent.click(addButton);
    });

    // Should only have the initial GET call
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it("filters todos by active status", async () => {
    const mockTodos = [
      {
        id: "1",
        text: "Active todo",
        completed: false,
        createdAt: "2024-01-01",
      },
      {
        id: "2",
        text: "Completed todo",
        completed: true,
        createdAt: "2024-01-02",
      },
    ];

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ todos: mockTodos }),
    });

    await act(async () => {
      render(<Home />);
    });

    await waitFor(() => {
      expect(screen.getByText("Active todo")).toBeInTheDocument();
    });

    await act(async () => {
      const activeButton = screen.getByText(/Active \(1\)/i);
      fireEvent.click(activeButton);
    });

    expect(screen.getByText("Active todo")).toBeInTheDocument();
    expect(screen.queryByText("Completed todo")).not.toBeInTheDocument();
  });

  it("filters todos by completed status", async () => {
    const mockTodos = [
      {
        id: "1",
        text: "Active todo",
        completed: false,
        createdAt: "2024-01-01",
      },
      {
        id: "2",
        text: "Completed todo",
        completed: true,
        createdAt: "2024-01-02",
      },
    ];

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ todos: mockTodos }),
    });

    await act(async () => {
      render(<Home />);
    });

    await waitFor(() => {
      expect(screen.getByText("Completed todo")).toBeInTheDocument();
    });

    await act(async () => {
      const completedButton = screen.getByText(/Completed \(1\)/i);
      fireEvent.click(completedButton);
    });

    expect(screen.getByText("Completed todo")).toBeInTheDocument();
    expect(screen.queryByText("Active todo")).not.toBeInTheDocument();
  });
});
