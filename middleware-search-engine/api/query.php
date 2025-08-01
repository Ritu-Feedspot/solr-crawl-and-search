<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

require_once '../utils/call_python.php';
require_once '../utils/sanitize.php';

function handleSearch() {
    try {
        $input = json_decode(file_get_contents('php://input'), true);

        if (!$input || !isset($input['query'])) {
            throw new Exception('Query parameter is required');
        }

        $query = $input['query'];  // DSL can be an array, don't sanitize
        $start = isset($input['start']) ? intval($input['start']) : 0;
        $rows = isset($input['rows']) ? intval($input['rows']) : 10;
        $sort = isset($input['sort']) ? $input['sort'] : null;

        $args = [
            'start' => $start,
            'rows' => $rows
        ];

        // Detect DSL vs simple search
        if (is_array($query) && isset($query['conditions'])) {
            $args['dsl_query'] = $query;
        } else {
            $args['query'] = sanitizeInput($query);  // Only sanitize simple strings
        }

        if ($sort) {
            $args['sort'] = $sort;
        }

        // Call Python script
        $pythonScript = "C:/RITU/solr-search-engine/backend-search-engine/query/query_solr_cloud.py";
        $result = callPythonScript($pythonScript, $args);

        if ($result === false) {
            throw new Exception('Failed to execute search');
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


function handleGet() {
    $query = isset($_GET['q']) ? sanitizeInput($_GET['q']) : '';
    $start = isset($_GET['start']) ? intval($_GET['start']) : 0;
    $rows = isset($_GET['rows']) ? intval($_GET['rows']) : 10;
    
    if (empty($query)) {
        echo json_encode([
            'error' => 'Query parameter is required',
            'docs' => [],
            'numFound' => 0
        ]);
        return;
    }
    
    $args = [
        'query' => $query,
        'start' => $start,
        'rows' => $rows
    ];
    
    $pythonScript = 'C:/RITU/solr-search-engine/backend-search-engine/query/query_solr_cloud.py';
    $result = callPythonScript($pythonScript, $args);
    
    if ($result === false) {
        http_response_code(500);
        echo json_encode([
            'error' => 'Failed to execute search',
            'docs' => [],
            'numFound' => 0
        ]);
    } else {
        echo $result;
    }
}

// Handle different HTTP methods
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    handleSearch();
} elseif ($_SERVER['REQUEST_METHOD'] === 'GET') {
    handleGet();
} else {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
}
?>