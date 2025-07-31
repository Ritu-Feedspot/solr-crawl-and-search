"use client"

export default function FacetFilters({ facets, selectedFacets, onFacetChange }) {
  if (!facets || Object.keys(facets).length === 0) {
    return null
  }

  return (
    <div className="facet-filters">
      <h3>Filter Results</h3>

      {Object.entries(facets).map(([facetField, facetValues]) => (
        <div key={facetField} className="facet-group">
          <h4 className="facet-title">{facetField.charAt(0).toUpperCase() + facetField.slice(1)}</h4>

          <div className="facet-options">
            {Object.entries(facetValues).map(([value, count]) => (
              <label key={value} className="facet-option">
                <input
                  type="checkbox"
                  checked={(selectedFacets[facetField] || []).includes(value)}
                  onChange={(e) => onFacetChange(facetField, value, e.target.checked)}
                />
                <span className="facet-label">
                  {value} ({count})
                </span>
              </label>
            ))}
          </div>
        </div>
      ))}

      {Object.keys(selectedFacets).length > 0 && (
        <button
          className="clear-filters"
          onClick={() => {
            Object.keys(selectedFacets).forEach((field) => {
              selectedFacets[field].forEach((value) => {
                onFacetChange(field, value, false)
              })
            })
          }}
        >
          Clear All Filters
        </button>
      )}
    </div>
  )
}
