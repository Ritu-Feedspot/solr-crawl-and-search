"use client"

import { useState } from "react"

export default function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState("")
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim()) {
      onSearch(query)
      setShowSuggestions(false)
    }
  }

  const handleInputChange = async (e) => {
    const value = e.target.value
    setQuery(value)

    if (value.length > 2) {
      try {
        const response = await fetch(
          `http://localhost:8081/middleware-search-engine/api/autocomplete.php?q=${encodeURIComponent(value)}`,
        )
        const data = await response.json()
        setSuggestions(data.suggestions || [])
        setShowSuggestions(true)
      } catch (error) {
        console.error("Autocomplete error:", error)
        setSuggestions([])
      }
    } else {
      setShowSuggestions(false)
    }
  }

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion)
    setShowSuggestions(false)
    onSearch(suggestion)
  }

  return (
    <div className="search-bar">
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-input-container">
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="Enter your search query..."
            className="search-input"
            disabled={loading}
          />
          <button type="submit" className="search-button" disabled={loading || !query.trim()}>
            {loading ? "Searching..." : "Search"}
          </button>
        </div>

        {showSuggestions && suggestions.length > 0 && (
          <div className="suggestions">
            {suggestions.map((suggestion, index) => (
              <div key={index} className="suggestion-item" onClick={() => handleSuggestionClick(suggestion)}>
                {suggestion}
              </div>
            ))}
          </div>
        )}
      </form>
    </div>
  )
}
