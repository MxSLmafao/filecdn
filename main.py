import os
from flask import Flask, request, send_from_directory, render_template_string, url_for, abort
from werkzeug.utils import secure_filename

# Configuration
UPLOAD_FOLDER = "/var/www/files"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "txt", "pdf", "mp4", "zip", "tar", "gz"}

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
    <title>File CDN</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background-color: #f4f4f9;
        }
        h1 { color: #333; }
        #drop-area {
            border: 2px dashed #ccc;
            border-radius: 20px;
            width: 80%;
            max-width: 600px;
            padding: 20px;
            text-align: center;
            font-size: 16px;
            background-color: white;
        }
        #fileElem { display: none; }
        #drop-area.highlight { border-color: purple; }
        p { margin: 10px 0; }
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
        ul { list-style: none; padding: 0; }
        li { margin: 5px 0; }
    </style>
</head>
<body>
    <h1>Upload Files</h1>
    <div id="drop-area">
        <p>Drag and drop files here or</p>
        <button onclick="fileInput.click()">Select Files</button>
        <input type="file" id="fileElem" multiple onchange="uploadFiles(this.files)">
    </div>
    <ul id="uploaded-files"></ul>

    <script>
        const dropArea = document.getElementById("drop-area");
        const uploadedFilesList = document.getElementById("uploaded-files");

        ["dragenter", "dragover"].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
            dropArea.addEventListener(eventName, highlight, false);
        });

        ["dragleave", "drop"].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
            dropArea.addEventListener(eventName, unhighlight, false);
        });

        dropArea.addEventListener("drop", handleDrop, false);

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        function highlight() {
            dropArea.classList.add("highlight");
        }

        function unhighlight() {
            dropArea.classList.remove("highlight");
        }

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            uploadFiles(files);
        }

        function uploadFiles(files) {
            Array.from(files).forEach(file => {
                const formData = new FormData();
                formData.append("file", file);

                fetch("/upload", {
                    method: "POST",
                    body: formData,
                })
                    .then(response => response.text())
                    .then(data => {
                        const li = document.createElement("li");
                        li.textContent = data;
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

def ensure_unique_filename(directory, filename):
    """Ensure the filename is unique in the target directory."""
    original_filename = filename
    counter = 1
    while os.path.exists(os.path.join(directory, filename)):
        name, ext = os.path.splitext(original_filename)
        filename = f"{name}({counter}){ext}"
        counter += 1
    return filename

@app.route("/", methods=["GET"])
def index():
    """Render the drag-and-drop upload page."""
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
        filename = secure_filename(file.filename)  # Secure the filename
        filename = ensure_unique_filename(app.config["UPLOAD_FOLDER"], filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        file_url = url_for("serve_file", filename=filename, _external=True)
        return file_url, 201

    return "File type not allowed", 400

@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename):
    """Serve files with correct headers for embedding."""
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(file_path):
        mime_type, _ = guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"  # Default for unknown files
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            filename,
            mimetype=mime_type,
            conditional=True,
        )
    abort(404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3690)
