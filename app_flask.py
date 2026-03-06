import os
from flask import Flask, send_from_directory

FRONTEND_DIR = "frontend"

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """
    Serve frontend files. If path is missing or not found, serve index.html (SPA-friendly).
    """
    if path != "" and os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")

if __name__ == "__main__":
    # Use 0.0.0.0 to make it reachable from other devices on the LAN.
    app.run(host="0.0.0.0", port=8000, debug=True)