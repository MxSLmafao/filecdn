import os
from flask import Flask, request, send_from_directory, render_template_string, url_for, abort
from werkzeug.utils import secure_filename

# Configuration
UPLOAD_FOLDER = "/var/www/files"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "txt", "pdf", "mp4", "zip", "tar", "gz"}
PORT = 3690

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# HTML Template for File Upload Page
UPLOAD_PAGE = """
<!doctype html>
<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File CDN</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            background-color: #f4f4f9;
        }
        h1 { color: #333; }
        #drop-area {
            border: 2px dashed #ccc;
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
            background-color: purple;
            color: white;
            border: none;
            cursor: pointer;
            border-radius: 5px;
        }
        button:hover { background-color: #5a1a7a; }
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
        @media screen and (max-width: 768px) {
            #drop-area {
                font-size: 14px;
            }
        }
    </style>
</head>
<body>
    <h1>Upload Files</h1>
    <div id="drop-area">
        <p>Drag and drop files here, or tap to select files</p>
        <button onclick="fileInput.click()">Select Files</button>
        <input type="file" id="fileInput" multiple onchange="uploadFiles(this.files)">
    </div>
    <ul id="uploaded-files"></ul>

    <script>
        const dropArea = document.getElementById("drop-area");
        const fileInput = document.getElementById("fileInput");
        const uploadedFilesList = document.getElementById("uploaded-files");

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

def allowed_file(filename):
    """Check if the file has a valid extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        return url_for("serve_file", filename=filename, _external=True), 201

    return "File type not allowed", 400

@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename):
    """Serve uploaded files."""
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(file_path):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
    abort(404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)