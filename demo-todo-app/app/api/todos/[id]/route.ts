import { NextRequest, NextResponse } from 'next/server'
import { incrementRequests, incrementErrors, recordDuration, setTodoCount } from '../../metrics/route'

interface Todo {
  id: number
  text: string
  completed: boolean
  createdAt: string
}

// This would be imported from a shared store in production
// For demo purposes, we'll access the parent route's storage
let todos: Todo[] = []

// Helper to get todos from parent route module
async function getTodos() {
  const response = await fetch('http://localhost:3000/api/todos')
  const data = await response.json()
  return data.todos
}

// GET /api/todos/[id] - Get a specific todo
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const startTime = Date.now()
  try {
    incrementRequests()
    const id = parseInt(params.id)
    const todos = await getTodos()
    const todo = todos.find((t: Todo) => t.id === id)

    if (!todo) {
      return NextResponse.json(
        { success: false, error: 'Todo not found' },
        { status: 404 }
      )
    }

    recordDuration(Date.now() - startTime)
    return NextResponse.json({ success: true, todo })
  } catch (error) {
    incrementErrors()
    console.error('Error fetching todo:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to fetch todo' },
      { status: 500 }
    )
  }
}

// PUT /api/todos/[id] - Update a todo
export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const startTime = Date.now()
  try {
    incrementRequests()
    const id = parseInt(params.id)
    const body = await request.json()
    const { text, completed } = body

    const todos = await getTodos()
    const todoIndex = todos.findIndex((t: Todo) => t.id === id)

    if (todoIndex === -1) {
      return NextResponse.json(
        { success: false, error: 'Todo not found' },
        { status: 404 }
      )
    }

    // Update fields
    if (text !== undefined) {
      todos[todoIndex].text = text.trim()
    }
    if (completed !== undefined) {
      todos[todoIndex].completed = completed
    }

    const completedCount = todos.filter((t: Todo) => t.completed).length
    setTodoCount(todos.length, completedCount)
    recordDuration(Date.now() - startTime)

    return NextResponse.json({
      success: true,
      todo: todos[todoIndex],
      message: 'Todo updated successfully',
    })
  } catch (error) {
    incrementErrors()
    console.error('Error updating todo:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to update todo' },
      { status: 500 }
    )
  }
}

// DELETE /api/todos/[id] - Delete a specific todo
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const startTime = Date.now()
  try {
    incrementRequests()
    const id = parseInt(params.id)
    const todos = await getTodos()
    const todoIndex = todos.findIndex((t: Todo) => t.id === id)

    if (todoIndex === -1) {
      return NextResponse.json(
        { success: false, error: 'Todo not found' },
        { status: 404 }
      )
    }

    todos.splice(todoIndex, 1)
    const completedCount = todos.filter((t: Todo) => t.completed).length
    setTodoCount(todos.length, completedCount)
    recordDuration(Date.now() - startTime)

    return NextResponse.json({
      success: true,
      message: 'Todo deleted successfully',
    })
  } catch (error) {
    incrementErrors()
    console.error('Error deleting todo:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to delete todo' },
      { status: 500 }
    )
  }
}
