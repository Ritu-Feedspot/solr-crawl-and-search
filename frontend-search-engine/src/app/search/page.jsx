"use client"

import { useSearchParams } from "next/navigation"
import { useEffect, useState } from "react"
import SearchBar from "../../components/SearchBar"
import SearchResult from "../../components/SearchResult"

export default function SearchPage() {
  const searchParams = useSearchParams()
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const query = searchParams.get("q")

  useEffect(() => {
    if (query) {
      handleSearch(query)
    }
  }, [query])

  const handleSearch = async (searchQuery) => {
    setLoading(true)
    try {
      const response = await fetch(`http://localhost:8081/middleware-search-engine/api/query.php`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: searchQuery,
          start: 0,
          rows: 20,
        }),
      })

      const data = await response.json()
      setResults(data.docs || [])
    } catch (error) {
      console.error("Search error:", error)
      setResults([])
    }
    setLoading(false)
  }

  return (
    <div className="search-page">
      <div className="container">
        <SearchBar onSearch={handleSearch} loading={loading} />
        <SearchResult results={results} />
      </div>
    </div>
  )
}
