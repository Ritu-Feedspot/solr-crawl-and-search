"use client"

import { useState } from "react"

export default function DSLBuilder({ onSearch, loading }) {
  const [dslQuery, setDslQuery] = useState({
    conditions: [{ field: "title", operator: "contains", value: "" }],
    sort: { field: "score", direction: "desc" },
    boost: [],
    facets: [],
  })

  const fields = ["title", "body", "url", "headings", "meta_description"]
  const operators = ["contains", "exact", "starts_with", "ends_with", "range"]
  const sortFields = ["score", "title", "lastModified", "url"]

  const addCondition = () => {
    setDslQuery((prev) => ({
      ...prev,
      conditions: [...prev.conditions, { field: "title", operator: "contains", value: "" }],
    }))
  }

  const updateCondition = (index, field, value) => {
    setDslQuery((prev) => ({
      ...prev,
      conditions: prev.conditions.map((condition, i) => (i === index ? { ...condition, [field]: value } : condition)),
    }))
  }

  const removeCondition = (index) => {
    setDslQuery((prev) => ({
      ...prev,
      conditions: prev.conditions.filter((_, i) => i !== index),
    }))
  }

  const addBoost = () => {
    setDslQuery((prev) => ({
      ...prev,
      boost: [...prev.boost, { field: "title", factor: 2.0 }],
    }))
  }

  const updateBoost = (index, field, value) => {
    setDslQuery((prev) => ({
      ...prev,
      boost: prev.boost.map((boost, i) => (i === index ? { ...boost, [field]: value } : boost)),
    }))
  }

  const removeBoost = (index) => {
    setDslQuery((prev) => ({
      ...prev,
      boost: prev.boost.filter((_, i) => i !== index),
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSearch(dslQuery, true)
  }

  return (
    <div className="dsl-builder">
      <h2>Advanced Search Builder</h2>

      <form onSubmit={handleSubmit} className="dsl-form">
        <div className="conditions-section">
          <h3>Search Conditions</h3>
          {dslQuery.conditions.map((condition, index) => (
            <div key={index} className="condition-row">
              <select
                value={condition.field}
                onChange={(e) => updateCondition(index, "field", e.target.value)}
                className="field-select"
              >
                {fields.map((field) => (
                  <option key={field} value={field}>
                    {field}
                  </option>
                ))}
              </select>

              <select
                value={condition.operator}
                onChange={(e) => updateCondition(index, "operator", e.target.value)}
                className="operator-select"
              >
                {operators.map((op) => (
                  <option key={op} value={op}>
                    {op.replace("_", " ")}
                  </option>
                ))}
              </select>

              <input
                type="text"
                value={condition.value}
                onChange={(e) => updateCondition(index, "value", e.target.value)}
                placeholder="Search value..."
                className="value-input"
              />

              {dslQuery.conditions.length > 1 && (
                <button type="button" onClick={() => removeCondition(index)} className="remove-btn">
                  Remove
                </button>
              )}
            </div>
          ))}

          <button type="button" onClick={addCondition} className="add-btn">
            Add Condition
          </button>
        </div>

        <div className="sort-section">
          <h3>Sort Results</h3>
          <div className="sort-row">
            <select
              value={dslQuery.sort.field}
              onChange={(e) =>
                setDslQuery((prev) => ({
                  ...prev,
                  sort: { ...prev.sort, field: e.target.value },
                }))
              }
              className="sort-field-select"
            >
              {sortFields.map((field) => (
                <option key={field} value={field}>
                  {field}
                </option>
              ))}
            </select>

            <select
              value={dslQuery.sort.direction}
              onChange={(e) =>
                setDslQuery((prev) => ({
                  ...prev,
                  sort: { ...prev.sort, direction: e.target.value },
                }))
              }
              className="sort-direction-select"
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>
        </div>

        <div className="boost-section">
          <h3>Field Boosting</h3>
          {dslQuery.boost.map((boost, index) => (
            <div key={index} className="boost-row">
              <select
                value={boost.field}
                onChange={(e) => updateBoost(index, "field", e.target.value)}
                className="boost-field-select"
              >
                {fields.map((field) => (
                  <option key={field} value={field}>
                    {field}
                  </option>
                ))}
              </select>

              <input
                type="number"
                value={boost.factor}
                onChange={(e) => updateBoost(index, "factor", Number.parseFloat(e.target.value))}
                min="0.1"
                max="10"
                step="0.1"
                className="boost-factor-input"
              />

              <button type="button" onClick={() => removeBoost(index)} className="remove-btn">
                Remove
              </button>
            </div>
          ))}

          <button type="button" onClick={addBoost} className="add-btn">
            Add Boost
          </button>
        </div>

        <div className="submit-section">
          <button
            type="submit"
            className="search-btn"
            disabled={loading || dslQuery.conditions.some((c) => !c.value.trim())}
          >
            {loading ? "Searching..." : "Search with DSL"}
          </button>
        </div>
      </form>
    </div>
  )
}
