# app_flask.py
from flask import Flask, send_from_directory, request, jsonify, abort
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

FRONTEND_DIR = "frontend"
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = None  # set to a set like {'pdf','docx'} to restrict

# create upload dir if missing
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)  # allow all origins for local dev; restrict in prod

def allowed(filename):
    if not ALLOWED_EXTENSIONS:
        return True
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """
    Serve frontend files. If path is missing or not found, serve index.html (SPA-friendly).
    """
    if path != "" and os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/api/search", methods=["POST"])
def api_search():
    """
    Example search endpoint. Replace the mock logic with your real search/indexing logic.
    Expects JSON: { "query": "..." }
    Returns: { "results": [ {...}, ... ] }
    """
    try:
        payload = request.get_json(force=True)
        q = (payload or {}).get("query", "").strip()
    except Exception:
        q = ""

    # --- Mock result(s). Replace with DB / index calls ---
    sample = [
        {
            "title": "US 2026 Statutory Holidays Calendar",
            "source": "Intranet",
            "date_added": "Oct 2025",
            "status": "Approved",
            "likes": 21,
            "dislikes": 2,
            "link": "#"
        },
        {
            "title": "Company Holiday Policy 2026",
            "source": "HR Docs",
            "date_added": "Nov 2025",
            "status": "Approved",
            "likes": 7,
            "dislikes": 0,
            "link": "#"
        }
    ]

    if q:
        filtered = [r for r in sample if q.lower() in r["title"].lower()]
    else:
        filtered = sample

    return jsonify({"results": filtered})

@app.route("/api/upload", methods=["POST"])
def api_upload():
    """
    Accept a multipart/form-data file with field name 'file'.
    Saves into uploads/ and returns a 'doc' object suitable for the frontend.
    """
    if "file" not in request.files:
        return jsonify({"error": "no file part"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "no selected file"}), 400
    if not allowed(f.filename):
        return jsonify({"error": "file type not allowed"}), 400

    filename = secure_filename(f.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)
    f.save(save_path)

    doc = {
        "title": filename,
        "source": "Uploaded",
        "date_added": "just now",
        "status": "Pending",
        "likes": 0,
        "dislikes": 0,
        "link": f"/uploads/{filename}"
    }
    return jsonify({"doc": doc}), 201

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Serve uploaded files back (for demo only)."""
    full = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(full):
        abort(404)
    return send_from_directory(UPLOAD_DIR, filename)

if __name__ == "__main__":
    # Use 0.0.0.0 to make it reachable from other devices on the LAN.
    app.run(host="0.0.0.0", port=8000, debug=True)