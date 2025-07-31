export function cn(...classes) {
  return classes.filter(Boolean).join(" ")
}

export function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

export function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  })
}

export function truncateText(text, maxLength = 200) {
  if (!text || text.length <= maxLength) return text
  return text.substring(0, maxLength) + "..."
}

export function highlightSearchTerms(text, searchTerms) {
  if (!searchTerms || !text) return text

  const terms = Array.isArray(searchTerms) ? searchTerms : [searchTerms]
  let highlightedText = text

  terms.forEach((term) => {
    const regex = new RegExp(`(${term})`, "gi")
    highlightedText = highlightedText.replace(regex, "<mark>$1</mark>")
  })

  return highlightedText
}
