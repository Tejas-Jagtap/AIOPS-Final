"use client";

import { useState, useEffect } from "react";
import styles from "./page.module.css";

interface Todo {
  id: number;
  text: string;
  completed: boolean;
  createdAt: string;
}

export default function Home() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [filter, setFilter] = useState<"all" | "active" | "completed">("all");
  const [loading, setLoading] = useState(false);

  // Load todos from API on mount
  useEffect(() => {
    loadTodos();
  }, []);

  const loadTodos = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/todos");
      if (response.ok) {
        const data = await response.json();
        setTodos(data.todos);
      }
    } catch (error) {
      console.error("Failed to load todos:", error);
    } finally {
      setLoading(false);
    }
  };

  const addTodo = async () => {
    if (inputValue.trim() === "") return;

    try {
      const response = await fetch("/api/todos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputValue }),
      });

      if (response.ok) {
        const data = await response.json();
        setTodos([...todos, data.todo]);
        setInputValue("");
      }
    } catch (error) {
      console.error("Failed to add todo:", error);
    }
  };

  const toggleTodo = async (id: number) => {
    try {
      const todo = todos.find((t) => t.id === id);
      if (!todo) return;

      const response = await fetch(`/api/todos/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ completed: !todo.completed }),
      });

      if (response.ok) {
        setTodos(
          todos.map((t) =>
            t.id === id ? { ...t, completed: !t.completed } : t
          )
        );
      }
    } catch (error) {
      console.error("Failed to toggle todo:", error);
    }
  };

  const deleteTodo = async (id: number) => {
    try {
      const response = await fetch(`/api/todos/${id}`, {
        method: "DELETE",
      });

      if (response.ok) {
        setTodos(todos.filter((t) => t.id !== id));
      }
    } catch (error) {
      console.error("Failed to delete todo:", error);
    }
  };

  const filteredTodos = todos.filter((todo) => {
    if (filter === "active") return !todo.completed;
    if (filter === "completed") return todo.completed;
    return true;
  });

  const activeCount = todos.filter((t) => !t.completed).length;

  return (
    <main className={styles.main}>
      <div className={styles.container}>
        <h1 className={styles.title}>AIOps Demo Todo App</h1>
        <p className={styles.subtitle}>
          Jenkins Pipeline Testing & Log Collection
        </p>

        <div className={styles.inputContainer}>
          <input
            type="text"
            className={styles.input}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && addTodo()}
            placeholder="What needs to be done?"
            disabled={loading}
          />
          <button
            className={styles.addButton}
            onClick={addTodo}
            disabled={loading}
          >
            Add
          </button>
        </div>

        <div className={styles.filters}>
          <button
            className={
              filter === "all" ? styles.filterActive : styles.filterButton
            }
            onClick={() => setFilter("all")}
          >
            All ({todos.length})
          </button>
          <button
            className={
              filter === "active" ? styles.filterActive : styles.filterButton
            }
            onClick={() => setFilter("active")}
          >
            Active ({activeCount})
          </button>
          <button
            className={
              filter === "completed" ? styles.filterActive : styles.filterButton
            }
            onClick={() => setFilter("completed")}
          >
            Completed ({todos.length - activeCount})
          </button>
        </div>

        {loading ? (
          <div className={styles.loading}>Loading todos...</div>
        ) : (
          <ul className={styles.todoList}>
            {filteredTodos.map((todo) => (
              <li key={todo.id} className={styles.todoItem}>
                <div className={styles.todoContent}>
                  <input
                    type="checkbox"
                    checked={todo.completed}
                    onChange={() => toggleTodo(todo.id)}
                    className={styles.checkbox}
                  />
                  <span
                    className={
                      todo.completed ? styles.completedText : styles.todoText
                    }
                  >
                    {todo.text}
                  </span>
                </div>
                <button
                  className={styles.deleteButton}
                  onClick={() => deleteTodo(todo.id)}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}

        {filteredTodos.length === 0 && !loading && (
          <div className={styles.emptyState}>
            {filter === "all"
              ? "No todos yet. Add one above!"
              : `No ${filter} todos.`}
          </div>
        )}
      </div>
    </main>
  );
}
