<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

require_once '../utils/call_python.php';
require_once '../utils/sanitize.php';

function handleDSLSearch() {
    try {
        $input = json_decode(file_get_contents('php://input'), true);
        
        if (!$input) {
            throw new Exception('Invalid JSON input');
        }
        
        // Handle nested query structure from frontend
        $dslQuery = null;
        if (isset($input['query']) && is_array($input['query'])) {
            // Frontend sends: {query: {conditions: [...], sort: {...}}, facets: {}, start: 0, rows: 10}
            $dslQuery = $input['query'];
        } else if (isset($input['conditions'])) {
            // Direct DSL structure: {conditions: [...], sort: {...}}
            $dslQuery = $input;
        } else {
            throw new Exception('DSL query structure not found');
        }

        if (!isset($dslQuery['conditions']) || !is_array($dslQuery['conditions'])) {
            throw new Exception('DSL conditions are required');
        }

        // Add pagination from top level
        $dslQuery['start'] = isset($input['start']) ? intval($input['start']) : 0;
        $dslQuery['rows'] = isset($input['rows']) ? intval($input['rows']) : 10;

        // Add facets from top level input to dslQuery
        if (isset($input['facets']) && is_array($input['facets'])) {
            $dslQuery['facets'] = $input['facets'];
        }

        // Sanitize DSL query
        $sanitizedQuery = sanitizeDSLQuery($dslQuery);
        
        // Call Python DSL query script
        $pythonScript = "C:/RITU/solr-search-engine/backend-search-engine/query/query_solr_cloud.py";
        $pythonArgs = ['dsl_query' => $sanitizedQuery];
        
        error_log("DSL Query being sent to Python: " . json_encode($pythonArgs));
        
        $result = callPythonScript($pythonScript, $pythonArgs);

        if ($result === false) {
            throw new Exception('Failed to execute DSL search - Python script error');
        }
        
        echo $result;
        
    } catch (Exception $e) {
        error_log("DSL Search Error: " . $e->getMessage());
        http_response_code(500);
        echo json_encode([
            'error' => $e->getMessage(),
            'docs' => [],
            'numFound' => 0
        ]);
    }
}

function sanitizeDSLQuery($input) {
    $sanitized = [];
    
    // Sanitize conditions
    if (isset($input['conditions'])) {
        $sanitized['conditions'] = [];
        foreach ($input['conditions'] as $condition) {
            if (isset($condition['field'], $condition['operator'], $condition['value'])) {
                $sanitized['conditions'][] = [
                    'field' => sanitizeInput($condition['field']),
                    'operator' => sanitizeInput($condition['operator']),
                    'value' => sanitizeInput($condition['value'])
                ];
            }
        }
    }
    
    // Sanitize sort
    if (isset($input['sort'])) {
        $sanitized['sort'] = [
            'field' => sanitizeInput($input['sort']['field'] ?? 'score'),
            'direction' => sanitizeInput($input['sort']['direction'] ?? 'desc')
        ];
    }
    
    // Sanitize boost
    if (isset($input['boost']) && is_array($input['boost'])) {
        $sanitized['boost'] = [];
        foreach ($input['boost'] as $boost) {
            if (isset($boost['field'], $boost['factor'])) {
                $sanitized['boost'][] = [
                    'field' => sanitizeInput($boost['field']),
                    'factor' => floatval($boost['factor'])
                ];
            }
        }
    }
    
    // Sanitize facets
    if (isset($input['facets']) && is_array($input['facets'])) {
        $sanitized['facets'] = [];
        foreach ($input['facets'] as $facetField => $facetValues) {
            $sanitizedFacetField = sanitizeInput($facetField);
            $sanitized['facets'][$sanitizedFacetField] = [];
            if (is_array($facetValues)) {
                foreach ($facetValues as $value) {
                    $sanitized['facets'][$sanitizedFacetField][] = sanitizeInput($value);
                }
            }
        }
    }

    // Add pagination
    $sanitized['start'] = isset($input['start']) ? intval($input['start']) : 0;
    $sanitized['rows'] = isset($input['rows']) ? intval($input['rows']) : 10;
    
    return $sanitized;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    handleDSLSearch();
} else {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
}
?>
