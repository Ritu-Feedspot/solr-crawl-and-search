<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

require_once '../utils/call_python.php';
require_once '../utils/sanitize.php';

function handleAutocomplete() {
    try {
        $query = isset($_GET['q']) ? sanitizeInput($_GET['q']) : '';
        $field = isset($_GET['field']) ? sanitizeInput($_GET['field']) : 'title';
        $limit = isset($_GET['limit']) ? intval($_GET['limit']) : 5;
        
        if (empty($query)) {
            echo json_encode(['suggestions' => []]);
            return;
        }
        
        if (strlen($query) < 2) {
            echo json_encode(['suggestions' => []]);
            return;
        }
        
        $args = [
            'query' => $query,
            'field' => $field,
            'limit' => $limit,
            'autocomplete' => true
        ];
        
        $pythonScript = '../../backend-search-engine/query/query_solr.py';
        $result = callPythonScript($pythonScript, $args);
        
        if ($result === false) {
            throw new Exception('Failed to get autocomplete suggestions');
        }
        
        echo $result;
        
    } catch (Exception $e) {
        http_response_code(500);
        echo json_encode([
            'error' => $e->getMessage(),
            'suggestions' => []
        ]);
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    handleAutocomplete();
} else {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
}
?>