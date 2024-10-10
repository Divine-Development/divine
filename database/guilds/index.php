<?php
// Define the password
$password = "Divine028";

// Check if the password is provided and correct
if (!isset($_POST['password']) || $_POST['password'] !== $password) {
    // If password is not provided or incorrect, show the login form
    ?>
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Protected JSON Files</title>
    </head>
    <body>
        <h1>Password Protected JSON Files</h1>
        <form method="POST">
            <label for="password">Enter Password:</label>
            <input type="password" id="password" name="password" required>
            <input type="submit" value="Submit">
        </form>
    </body>
    </html>
    <?php
    exit(); // Exit if the password is incorrect or not provided
}

// If the correct password is provided, list and provide links to JSON files
$jsonFiles = glob("*.json"); // Find all .json files in the current directory

if (empty($jsonFiles)) {
    echo "No JSON files found in this directory.";
} else {
    echo "<h1>JSON Files</h1>";
    echo "<ul>";
    foreach ($jsonFiles as $file) {
        // Create a link to view each JSON file, passing the file name in the URL
        echo "<li><a href='view_json.php?file=" . urlencode($file) . "'>" . htmlspecialchars($file) . "</a></li>";
    }
    echo "</ul>";
}
?>