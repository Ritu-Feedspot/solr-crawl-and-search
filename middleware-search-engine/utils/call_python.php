<?php

function callPythonScript($scriptPath, $args = []) {
    try {
        if (!file_exists($scriptPath)) {
            error_log("Python script not found: $scriptPath");
            return false;
        }

        $pythonPath = 'python'; // or 'python3' depending on system
        $command = escapeshellcmd($pythonPath) . ' ' . escapeshellarg($scriptPath);

        if (!empty($args)) {
            $jsonArgs = json_encode($args);
            $command .= ' ' . escapeshellarg($jsonArgs);
        }

        $output = [];
        $returnCode = 0;
        exec($command . ' 2>&1', $output, $returnCode);

        if ($returnCode !== 0) {
            error_log("Python script failed with code $returnCode: " . implode("\n", $output));
            return false;
        }

        $result = implode("\n", $output);

        $decoded = json_decode($result, true);
        if (json_last_error() === JSON_ERROR_NONE) {
            return json_encode($decoded);
        }

        return $result;

    } catch (Exception $e) {
        error_log("Error calling Python script: " . $e->getMessage());
        return false;
    }
}

function validatePythonEnvironment() {
    $pythonPath = 'python';
    $command = escapeshellcmd($pythonPath) . ' --version 2>&1';

    exec($command, $output, $returnCode);

    if ($returnCode === 0) {
        return true;
    }

    error_log("Python not found or not working properly");
    return false;
}
?>
