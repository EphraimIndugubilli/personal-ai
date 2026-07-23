import { useEffect, useRef, useState } from 'react'
import './App.css'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  const data = await response.json().catch(() => ({}))

  if (!response.ok || data.error) {
    throw new Error(data.detail || data.error || 'Something went wrong. Please try again.')
  }

  return data
}

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello, Ephra. I am ready to help you build and remember what matters.',
    },
  ])
  const [message, setMessage] = useState('')
  const [memories, setMemories] = useState([])
  const [memoryDraft, setMemoryDraft] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editingText, setEditingText] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isSavingMemory, setIsSavingMemory] = useState(false)
  const [error, setError] = useState('')
  const chatEndRef = useRef(null)

  useEffect(() => {
    loadMemories()
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isSending])

  async function loadMemories() {
    try {
      setMemories(await request('/memories'))
    } catch (err) {
      setError(`Could not load memories: ${err.message}`)
    }
  }

  async function sendMessage(event) {
    event.preventDefault()
    const text = message.trim()
    if (!text || isSending) return

    setError('')
    setMessage('')
    setMessages((current) => [...current, { role: 'user', content: text }])
    setIsSending(true)

    try {
      const data = await request('/chat', {
        method: 'POST',
        body: JSON.stringify({ message: text }),
      })
      setMessages((current) => [...current, { role: 'assistant', content: data.reply }])
    } catch (err) {
      setError(`Chat failed: ${err.message}`)
    } finally {
      setIsSending(false)
    }
  }

  async function addMemory(event) {
    event.preventDefault()
    const text = memoryDraft.trim()
    if (!text || isSavingMemory) return

    setError('')
    setIsSavingMemory(true)
    try {
      await request('/remember/', { method: 'POST', body: JSON.stringify({ text }) })
      setMemoryDraft('')
      await loadMemories()
    } catch (err) {
      setError(`Could not save memory: ${err.message}`)
    } finally {
      setIsSavingMemory(false)
    }
  }

  async function saveMemory(memoryId) {
    const text = editingText.trim()
    if (!text) return

    setError('')
    try {
      await request(`/memories/${memoryId}`, {
        method: 'PUT',
        body: JSON.stringify({ text }),
      })
      setEditingId(null)
      setEditingText('')
      await loadMemories()
    } catch (err) {
      setError(`Could not update memory: ${err.message}`)
    }
  }

  async function removeMemory(memoryId) {
    if (!window.confirm('Delete this memory permanently?')) return

    setError('')
    try {
      await request(`/memories/${memoryId}`, { method: 'DELETE' })
      await loadMemories()
    } catch (err) {
      setError(`Could not delete memory: ${err.message}`)
    }
  }

  return (
    <main className="app-shell">
      <section className="chat-panel">
        <header className="app-header">
          <div className="eyebrow">PERSONAL AI</div>
          <h1>Your thinking partner</h1>
          <p>Private context, persistent memory, and a conversation that picks up where you left off.</p>
        </header>

        <div className="conversation" aria-live="polite">
          {messages.map((item, index) => (
            <article className={`message ${item.role}`} key={`${item.role}-${index}`}>
              <span className="message-label">{item.role === 'assistant' ? 'AI' : 'YOU'}</span>
              <p>{item.content}</p>
            </article>
          ))}
          {isSending && <div className="typing">Thinking<span>.</span><span>.</span><span>.</span></div>}
          <div ref={chatEndRef} />
        </div>

        <form className="composer" onSubmit={sendMessage}>
          <label htmlFor="chat-message">Message your assistant</label>
          <div className="composer-row">
            <textarea
              id="chat-message"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Ask anything…"
              rows="2"
              disabled={isSending}
            />
            <button type="submit" disabled={!message.trim() || isSending}>
              {isSending ? 'Sending' : 'Send'}
            </button>
          </div>
        </form>
      </section>

      <aside className="memory-panel">
        <header>
          <div className="eyebrow">LONG-TERM CONTEXT</div>
          <h2>Memory bank</h2>
          <p>Facts your assistant can use when they are relevant.</p>
        </header>

        <form className="memory-form" onSubmit={addMemory}>
          <label htmlFor="new-memory">Add a memory</label>
          <textarea
            id="new-memory"
            value={memoryDraft}
            onChange={(event) => setMemoryDraft(event.target.value)}
            placeholder="For example: I prefer concise answers."
            rows="3"
          />
          <button type="submit" disabled={!memoryDraft.trim() || isSavingMemory}>
            {isSavingMemory ? 'Saving…' : 'Save memory'}
          </button>
        </form>

        <div className="memory-list">
          {memories.length === 0 ? (
            <p className="empty-state">No saved memories yet.</p>
          ) : (
            memories.map((memory) => (
              <article className="memory-card" key={memory.id}>
                {editingId === memory.id ? (
                  <>
                    <textarea
                      value={editingText}
                      onChange={(event) => setEditingText(event.target.value)}
                      rows="3"
                      aria-label="Edit memory"
                    />
                    <div className="memory-actions">
                      <button className="text-button" type="button" onClick={() => saveMemory(memory.id)}>Save</button>
                      <button className="text-button muted" type="button" onClick={() => setEditingId(null)}>Cancel</button>
                    </div>
                  </>
                ) : (
                  <>
                    <p>{memory.content}</p>
                    <div className="memory-actions">
                      <button className="text-button" type="button" onClick={() => {
                        setEditingId(memory.id)
                        setEditingText(memory.content)
                      }}>Edit</button>
                      <button className="text-button danger" type="button" onClick={() => removeMemory(memory.id)}>Delete</button>
                    </div>
                  </>
                )}
              </article>
            ))
          )}
        </div>
      </aside>

      {error && <div className="error-banner" role="alert">{error}</div>}
    </main>
  )
}

export default App
