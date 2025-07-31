"use client"

import { useState } from "react"
import SearchBar from "../components/SearchBar"
import SearchResult from "../components/SearchResult"
import FacetFilters from "../components/FacetFilters"
import DSLBuilder from "../components/DSLBuilder"

export default function HomePage() {
  const [searchResults, setSearchResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [facets, setFacets] = useState({})
  const [selectedFacets, setSelectedFacets] = useState({})
  const [showDSL, setShowDSL] = useState(false)

  const handleSearch = async (query, isDSL = false) => {
    setLoading(true)
    try {
      const endpoint = isDSL ? "/api/dsl.php" : "/api/query.php"
      const response = await fetch(`http://localhost:8081/middleware-search-engine${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
          facets: selectedFacets,
          start: 0,
          rows: 10,
        }),
      })

      const data = await response.json()
      setSearchResults(data.docs || [])
      setFacets(data.facets || {})
    } catch (error) {
      console.error("Search error:", error)
      setSearchResults([])
    }
    setLoading(false)
  }

  const handleFacetChange = (facetField, facetValue, checked) => {
    setSelectedFacets((prev) => ({
      ...prev,
      [facetField]: checked
        ? [...(prev[facetField] || []), facetValue]
        : (prev[facetField] || []).filter((v) => v !== facetValue),
    }))
  }

  return (
    <div className="search-engine">
      <header className="header">
        <div className="container">
          <h1>Solr Search Engine</h1>
          <div className="search-controls">
            <button onClick={() => setShowDSL(!showDSL)} className={`toggle-btn ${showDSL ? "active" : ""}`}>
              {showDSL ? "Simple Search" : "Advanced DSL"}
            </button>
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="container">
          {!showDSL ? (
            <SearchBar onSearch={handleSearch} loading={loading} />
          ) : (
            <DSLBuilder onSearch={handleSearch} loading={loading} />
          )}

          <div className="search-layout">
            <aside className="sidebar">
              <FacetFilters facets={facets} selectedFacets={selectedFacets} onFacetChange={handleFacetChange} />
            </aside>

            <section className="results">
              {loading ? <div className="loading">Searching...</div> : <SearchResult results={searchResults} />}
            </section>
          </div>
        </div>
      </main>
    </div>
  )
}
