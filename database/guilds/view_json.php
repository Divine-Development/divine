<?php
// Define the same password used in index.php
$password = "Divine028";

// Ensure the password is rechecked for security
if (!isset($_POST['password']) || $_POST['password'] !== $password) {
    header("Location: index.php"); // Redirect back to index if the password is incorrect
    exit();
}

// Check if the file parameter is provided and it matches a valid JSON file name pattern
if (isset($_GET['file']) && preg_match("/^[a-zA-Z0-9_-]+\\.json$/", $_GET['file'])) {
    $file = $_GET['file'];
    
    // Check if the file exists and read its contents
    if (file_exists($file)) {
        $content = file_get_contents($file);
        header("Content-Type: application/json"); // Set header for JSON content
        echo $content; // Output the file's content
    } else {
        echo "File not found."; // Handle case where the file doesn't exist
    }
} else {
    echo "Invalid file request."; // Handle invalid file names
}
?>
