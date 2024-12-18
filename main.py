import os
from flask import Flask, request, send_file, render_template_string, url_for, abort
from werkzeug.utils import secure_filename
from mimetypes import guess_type

# Configuration
UPLOAD_FOLDER = "/var/www/files"
MEDIA_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "wmv", "flv", "webm", "mp3", "wav", "ogg", "m4a", "flac", "aac", "png", "jpg", "jpeg", "gif", "bmp", "pdf", "txt"}
PORT = 3690

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    """Check if the file has a valid media extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in MEDIA_EXTENSIONS

def get_mime_type(filepath):
    """Ensure correct MIME type, especially for media files like mp4."""
    mime_type, _ = guess_type(filepath)
    if filepath.endswith(".mp4") and mime_type != "video/mp4":
        return "video/mp4"
    return mime_type or "application/octet-stream"

# HTML Template for File Upload Page
UPLOAD_PAGE = """
<!doctype html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Media CDN</title>
    <style>
        :root {
            --bg-color: #f4f4f9;
            --text-color: #333;
            --border-color: #ccc;
            --button-bg: purple;
            --button-hover-bg: #5a1a7a;
        }
        [data-theme="dark"] {
            --bg-color: #121212;
            --text-color: #ffffff;
            --border-color: #444;
            --button-bg: #bb86fc;
            --button-hover-bg: #9a67ea;
        }
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            background-color: var(--bg-color);
            color: var(--text-color);
        }
        h1 { color: var(--text-color); }
        #drop-area {
            border: 2px dashed var(--border-color);
            border-radius: 20px;
            width: 90%;
            max-width: 600px;
            padding: 20px;
            text-align: center;
            background-color: white;
            margin: 10px 0;
        }
        #drop-area.highlight { border-color: purple; }
        input[type="file"] {
            display: none;
        }
        button {
            margin-top: 10px;
            padding: 10px 20px;
            background-color: var(--button-bg);
            color: white;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }
        button:hover { background-color: var(--button-hover-bg); }
        ul {
            list-style: none;
            padding: 0;
            margin-top: 10px;
            width: 100%;
            max-width: 600px;
        }
        li {
            margin: 5px 0;
            word-wrap: break-word;
        }
        #theme-toggle {
            position: absolute;
            top: 10px;
            right: 10px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 24px;
            color: var(--text-color);
        }
        @media screen and (max-width: 768px) {
            #drop-area {
                font-size: 14px;
            }
        }
    </style>
</head>
<body>
    <button id="theme-toggle">🌙</button>
    <h1>Upload Media Files</h1>
    <div id="drop-area">
        <p>Drag and drop media files here, or tap to select files</p>
        <button onclick="fileInput.click()">Select Files</button>
        <input type="file" id="fileInput" multiple onchange="uploadFiles(this.files)">
    </div>
    <ul id="uploaded-files"></ul>

    <script>
        const dropArea = document.getElementById("drop-area");
        const fileInput = document.getElementById("fileInput");
        const uploadedFilesList = document.getElementById("uploaded-files");
        const themeToggle = document.getElementById("theme-toggle");

        // Theme toggle
        themeToggle.addEventListener("click", () => {
            const isDark = document.body.dataset.theme === "dark";
            document.body.dataset.theme = isDark ? "light" : "dark";
            themeToggle.textContent = isDark ? "🌙" : "☀️";
        });

        // Prevent default drag behaviors
        ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });

        // Highlight drop area on drag events
        ["dragenter", "dragover"].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.add("highlight"), false);
        });

        ["dragleave", "drop"].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.remove("highlight"), false);
        });

        // Handle dropped files
        dropArea.addEventListener("drop", handleDrop, false);

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        function handleDrop(e) {
            const files = e.dataTransfer.files;
            uploadFiles(files);
        }

        function uploadFiles(files) {
            Array.from(files).forEach(file => {
                const formData = new FormData();
                formData.append("file", file);

                fetch("/upload", {
                    method: "POST",
                    body: formData
                })
                    .then(response => response.text())
                    .then(data => {
                        const li = document.createElement("li");
                        li.innerHTML = `<a href="${data}" target="_blank">${data}</a>`;
                        uploadedFilesList.appendChild(li);
                    })
                    .catch(() => alert("Error uploading file."));
            });
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    """Render the upload page."""
    return render_template_string(UPLOAD_PAGE)

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file uploads."""
    if "file" not in request.files:
        return "No file part", 400

    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400

    # Check if the file extension is allowed
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        return url_for("serve_file", filename=filename, _external=True), 201

    return "File type not allowed", 400

@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename):
    """Serve uploaded files with the correct MIME type."""
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(file_path):
        mime_type = get_mime_type(file_path)
        return send_file(
            file_path,
            mimetype=mime_type,
            as_attachment=False  # Serve inline
        )
    abort(404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
