"use client"

export default function Pagination({ currentPage, totalPages, totalResults, resultsPerPage, onPageChange, loading }) {
  const startResult = (currentPage - 1) * resultsPerPage + 1
  const endResult = Math.min(currentPage * resultsPerPage, totalResults)

  const handlePrevious = () => {
    if (currentPage > 1 && !loading) {
      onPageChange(currentPage - 1)
    }
  }

  const handleNext = () => {
    if (currentPage < totalPages && !loading) {
      onPageChange(currentPage + 1)
    }
  }

  const handlePageClick = (page) => {
    if (page !== currentPage && !loading) {
      onPageChange(page)
    }
  }

  // Generate page numbers to show
  const getPageNumbers = () => {
    const pages = []
    const maxPagesToShow = 5

    if (totalPages <= maxPagesToShow) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      // Show pages around current page
      let startPage = Math.max(1, currentPage - 2)
      let endPage = Math.min(totalPages, currentPage + 2)

      // Adjust if we're near the beginning or end
      if (currentPage <= 3) {
        endPage = Math.min(totalPages, 5)
      }
      if (currentPage >= totalPages - 2) {
        startPage = Math.max(1, totalPages - 4)
      }

      // Add first page and ellipsis if needed
      if (startPage > 1) {
        pages.push(1)
        if (startPage > 2) {
          pages.push("...")
        }
      }

      // Add middle pages
      for (let i = startPage; i <= endPage; i++) {
        pages.push(i)
      }

      // Add last page and ellipsis if needed
      if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
          pages.push("...")
        }
        pages.push(totalPages)
      }
    }

    return pages
  }

  if (totalPages <= 1) {
    return null
  }

  return (
    <div className="pagination">
      <div className="pagination-info">
        <span>
          Page {currentPage} of {totalPages} ({totalResults} total results)
        </span>
      </div>

      <div className="pagination-controls">
        <button
          className={`pagination-btn ${currentPage === 1 || loading ? "disabled" : ""}`}
          onClick={handlePrevious}
          disabled={currentPage === 1 || loading}
          aria-label="Previous page"
        >
          ← Previous
        </button>

        <div className="pagination-numbers">
          {getPageNumbers().map((page, index) => (
            <button
              key={index}
              className={`pagination-number ${
                page === currentPage ? "active" : ""
              } ${page === "..." ? "ellipsis" : ""} ${loading ? "disabled" : ""}`}
              onClick={() => page !== "..." && handlePageClick(page)}
              disabled={page === "..." || loading}
            >
              {page}
            </button>
          ))}
        </div>

        <button
          className={`pagination-btn ${currentPage === totalPages || loading ? "disabled" : ""}`}
          onClick={handleNext}
          disabled={currentPage === totalPages || loading}
          aria-label="Next page"
        >
          Next →
        </button>
      </div>
    </div>
  )
}
