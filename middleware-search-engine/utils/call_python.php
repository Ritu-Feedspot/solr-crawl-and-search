<?php

function callPythonScript($scriptPath, $args = []) {
    try {
        if (!file_exists($scriptPath)) {
            error_log("Python script not found: $scriptPath");
            return false;
        }

        $pythonPath = 'C:\RITU\solr-search-engine\backend-search-engine\venv\Scripts\python.exe';
        $command = escapeshellcmd($pythonPath) . ' ' . escapeshellarg($scriptPath);

        if (!empty($args)) {
            $jsonArgs = base64_encode(json_encode($args));
            $command .= ' ' . escapeshellarg($jsonArgs);
        }

        $output = [];
        $returnCode = 0;
        exec($command . ' 2>&1', $output, $returnCode);

        $result = implode("\n", $output);

        if ($returnCode !== 0) {
            error_log("Python script failed with code $returnCode: $result");
            return false;
        }

        // Ensure it's valid JSON before returning
        $decoded = json_decode($result, true);
        if (json_last_error() === JSON_ERROR_NONE) {
            return json_encode($decoded); // Re-encode for safety
        } else {
            error_log("Invalid JSON from Python: $result");
            return false;
        }

    } catch (Exception $e) {
        error_log("Error calling Python script: " . $e->getMessage());
        return false;
    }
}


?>
