export default function SearchResult({ results, totalResults, currentPage, resultsPerPage }) {
  if (!results || results.length === 0) {
    return (
      <div className="no-results">
        <p>No results found. Try adjusting your search terms.</p>
      </div>
    )
  }

  const startResult = (currentPage - 1) * resultsPerPage + 1
  const endResult = Math.min(currentPage * resultsPerPage, totalResults)

  const highlightText = (text, query) => {
    if (!query || !text) return text
    const regex = new RegExp(`(${query})`, "gi")
    return text.replace(regex, "<mark>$1</mark>")
  }

  return (
    <div className="search-results">
      <div className="results-header">
        <p>
          Showing {startResult}-{endResult} of {totalResults} results
        </p>
      </div>

      <div className="results-list">
        {results.map((result, index) => (
          <div key={result.id || index} className="result-item">
            <h3 className="result-title">
              <a
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                dangerouslySetInnerHTML={{
                  __html: result.title || "Untitled",
                }}
              />
            </h3>

            <p className="result-url">{result.url}</p>

            <p
              className="result-snippet"
              dangerouslySetInnerHTML={{
                __html: result.body || result.content || "No content available",
              }}
            />

            {result.last_modified && (
              <p className="result-date">Last modified: {new Date(result.last_modified).toLocaleDateString()}</p>
            )}

            {result.domain && <p className="result-domain">Domain: {result.domain}</p>}
            {result.score && <p className="result-score">Relevance: {(result.score * 100).toFixed(1)}%</p>}

          </div>
        ))}
      </div>
    </div>
  )
}
