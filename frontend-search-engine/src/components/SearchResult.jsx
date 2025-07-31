export default function SearchResult({ results }) {
  if (!results || results.length === 0) {
    return (
      <div className="no-results">
        <p>No results found. Try adjusting your search terms.</p>
      </div>
    )
  }

  const highlightText = (text, query) => {
    if (!query || !text) return text
    const regex = new RegExp(`(${query})`, "gi")
    return text.replace(regex, "<mark>$1</mark>")
  }

  return (
    <div className="search-results">
      <div className="results-header">
        <p>{results.length} results found</p>
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
                  __html: highlightText(result.title, result.query),
                }}
              />
            </h3>

            <p className="result-url">{result.url}</p>

            <p
              className="result-snippet"
              dangerouslySetInnerHTML={{
                __html: highlightText(result.body || result.content, result.query),
              }}
            />

            {result.lastModified && (
              <p className="result-date">Last modified: {new Date(result.lastModified).toLocaleDateString()}</p>
            )}

            {/* {result.score && <p className="result-score">Relevance: {(result.score * 100).toFixed(1)}%</p>} */}
          </div>
        ))}
      </div>
    </div>
  )
}
