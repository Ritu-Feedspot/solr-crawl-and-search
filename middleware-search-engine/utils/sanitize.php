<?php

function sanitizeInput($input) {
    if (is_string($input)) {
        // Remove potentially dangerous characters
        $input = strip_tags($input);
        $input = htmlspecialchars($input, ENT_QUOTES, 'UTF-8');
        $input = trim($input);
        
        // Remove SQL injection attempts
        $dangerous_patterns = [
            '/(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)/i',
            '/[<>"\']/',
            '/javascript:/i',
            '/vbscript:/i',
            '/onload/i',
            '/onerror/i'
        ];
        
        foreach ($dangerous_patterns as $pattern) {
            $input = preg_replace($pattern, '', $input);
        }
        
        return $input;
    }
    
    return $input;
}

function validateSearchQuery($query) {
    if (empty($query) || !is_string($query)) {
        return false;
    }
    
    // Check minimum length
    if (strlen(trim($query)) < 1) {
        return false;
    }
    
    // Check maximum length
    if (strlen($query) > 500) {
        return false;
    }
    
    return true;
}

function validateField($field) {
    $allowedFields = ['title', 'body', 'url', 'headings', 'meta_description'];
    return in_array($field, $allowedFields);
}

function validateOperator($operator) {
    $allowedOperators = ['contains', 'exact', 'starts_with', 'ends_with', 'range'];
    return in_array($operator, $allowedOperators);
}

function validateSortField($field) {
    $allowedSortFields = ['score', 'title', 'lastModified', 'url'];
    return in_array($field, $allowedSortFields);
}

function validateSortDirection($direction) {
    return in_array(strtolower($direction), ['asc', 'desc']);
}
?>