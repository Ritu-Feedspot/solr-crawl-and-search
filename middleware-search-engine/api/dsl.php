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
        
        // Validate DSL structure
        // if (!isset($input['conditions']) || !is_array($input['conditions'])) {
        //     throw new Exception('DSL conditions are required');
        // }

        $payload = isset($input['query']) ? $input['query'] : $input;

        if (!isset($payload['conditions']) || !is_array($payload['conditions'])) {
            throw new Exception('DSL conditions are required');
        }

        // Sanitize DSL query
        $dslQuery = sanitizeDSLQuery($payload);

        
        // // Sanitize DSL query
        // $dslQuery = sanitizeDSLQuery($input);
        
        // Call Python DSL query script
        // $pythonScript = "C:/RITU/solr-search-engine/backend-search-engine/query/query_solr_cloud.py";
        // $result = callPythonScript($pythonScript, ['dsl_query' => $dslQuery]);

        $pythonScript = "C:/RITU/solr-search-engine/backend-search-engine/query/query_solr_cloud.py";
        $pythonArgs = ['dsl_query' => $dslQuery];
        error_log("Sending to Python: " . json_encode($pythonArgs));
        $result = callPythonScript($pythonScript, $pythonArgs);


        if ($result === false) {
            throw new Exception('Failed to execute DSL search');
        }
        
        echo $result;
        
    } catch (Exception $e) {
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