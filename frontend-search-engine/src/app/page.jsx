"use client"

import { useState } from "react"
import SearchBar from "../components/SearchBar"
import SearchResult from "../components/SearchResult"
import FacetFilters from "../components/FacetFilters"
import DSLBuilder from "../components/DSLBuilder"
import Pagination from "../components/Pagination"

export default function HomePage() {
  const [searchResults, setSearchResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [facets, setFacets] = useState({})
  const [selectedFacets, setSelectedFacets] = useState({})
  const [searchMode, setSearchMode] = useState('keyowrd')
  // const [showDSL, setShowDSL] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalResults, setTotalResults] = useState(0)
  const [currentQuery, setCurrentQuery] = useState(null)
  const [currentSearchModeForQuery, setCurrentSearchModeForQuery] = useState('keyword')
  // const [isDSLQuery, setIsDSLQuery] = useState(false)

  const resultsPerPage = 5

  const handleSearch = async (query, mode = 'keyword', page = 1, facetsOverride = null) => {
    setLoading(true)
    setCurrentQuery(query)
    setCurrentSearchModeForQuery(mode)
    // setIsDSLQuery(isDSL)
    setCurrentPage(page)

    const facetsToUse = facetsOverride !== null ? facetsOverride : selectedFacets

    let endpoint = "/api/query.php"
    let requestBody = {
      start: (page - 1) * resultsPerPage,
      rows: resultsPerPage,
      facets: facetsToUse
    }

    if (mode === 'dsl') {
      endpoint = "/api/dsl.php"
      requestBody.query = query //Request body is the dsl object
    } else if (mode === "semantic") {
      requestBody.query = query // query is the text string 
      requestBody.semantic_search = true
    } else { // keyword mode (default)
      requestBody.query = query
    }

    try {
      const response = await fetch(`http://localhost:8081/middleware-search-engine${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      })

      const data = await response.json()
      setSearchResults(data.docs || [])
      setFacets(data.facets || {})
      setTotalResults(data.numFound || 0)
    } catch (error) {
      console.error("Search error:", error)
      setSearchResults([])
      setTotalResults(0)
    }
    setLoading(false)
  }

  const handlePageChange = (newPage) => {
    if (currentQuery) {
      // Use the mode that was active when the currentQuery was set
      handleSearch(currentQuery, currentSearchModeForQuery, newPage, selectedFacets)
    }
  }

  const handleFacetChange = (facetField, facetValue, checked) => {
    const newSelectedFacets = { ...selectedFacets }
    if (checked) {
      newSelectedFacets[facetField] = [...(newSelectedFacets[facetField] || []), facetValue]
    } else {
      newSelectedFacets[facetField] = (newSelectedFacets[facetField] || []).filter((v) => v !== facetValue)
    }

    // Update the state
    setSelectedFacets(newSelectedFacets)

    // Re-run search with the NEWLY calculated facets, resetting to page 1
    if (currentQuery) {
      handleSearch(currentQuery, currentSearchModeForQuery, 1, newSelectedFacets)
    }
  }

  const totalPages = Math.ceil(totalResults / resultsPerPage)

  return (
    <div className="search-engine">
      <header className="header">
        <div className="container">
          <h1>Solr Search Engine</h1>
          <div className="search-controls">
            <button
              onClick={() => setSearchMode('keyword')}
              className={`toggle-btn ${searchMode === 'keyword' ? "active" : ""}`}
            >
              Keyword Search
            </button>
            <button
              onClick={() => setSearchMode('dsl')}
              className={`toggle-btn ${searchMode === 'dsl' ? "active" : ""}`}
            >
              Advanced DSL
            </button>
            <button
              onClick={() => setSearchMode('semantic')}
              className={`toggle-btn ${searchMode === 'semantic' ? "active" : ""}`}
            >
              Semantic Search
            </button>
            
            {/* <button onClick={() => setShowDSL(!showDSL)} className={`toggle-btn ${showDSL ? "active" : ""}`}>
              {showDSL ? "Simple Search" : "Advanced DSL"}
            </button> */}
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="container">
          {searchMode === 'dsl' ? (
            <DSLBuilder onSearch={(query) => handleSearch(query, 'dsl')} loading={loading} />
          ) : (
            <SearchBar onSearch={(query) => handleSearch(query, searchMode)} loading={loading} />            
          )}

          <div className="search-layout">
            <aside className="sidebar">
              <FacetFilters facets={facets} selectedFacets={selectedFacets} onFacetChange={handleFacetChange} />
            </aside>

            <section className="results">
              {loading ? (
                <div className="loading">Searching...</div>
              ) : (
                <>
                  <SearchResult
                    results={searchResults}
                    totalResults={totalResults}
                    currentPage={currentPage}
                    resultsPerPage={resultsPerPage}
                  />
                  {totalResults > resultsPerPage && (
                    <Pagination
                      currentPage={currentPage}
                      totalPages={totalPages}
                      totalResults={totalResults}
                      resultsPerPage={resultsPerPage}
                      onPageChange={handlePageChange}
                      loading={loading}
                    />
                  )}
                </>
              )}
            </section>
          </div>
        </div>
      </main>
    </div>
  )
}
