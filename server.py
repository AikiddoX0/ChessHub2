import csv
import json
import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
JSON_PATH = DATA_DIR / "registrations.json"
CSV_PATH = DATA_DIR / "registrations.csv"
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 8001))

# Email configuration
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "aikiddox@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "Mayanksir00")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "aikiddox@gmail.com")

FIELDS = [
    "submitted_at",
    "full_name",
    "whatsapp",
    "username",
    "payment_id",
    "note",
]


def ensure_storage():
    DATA_DIR.mkdir(exist_ok=True)

    if not JSON_PATH.exists():
        JSON_PATH.write_text("[]", encoding="utf-8")

    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
            writer.writeheader()


def load_registrations():
    ensure_storage()
    try:
        return json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_registration(entry):
    registrations = load_registrations()
    registrations.append(entry)
    JSON_PATH.write_text(json.dumps(registrations, indent=2), encoding="utf-8")

    with CSV_PATH.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
        writer.writerow(entry)


def send_email_notification(entry):
    try:
        subject = f"New ChessHub Registration: {entry['full_name']}"
        body = f"""
New Registration Received!

Full Name: {entry['full_name']}
WhatsApp: {entry['whatsapp']}
Username: {entry['username']}
Payment ID: {entry['payment_id']}
Note: {entry['note']}
Submitted At: {entry['submitted_at']}
"""
        msg = MIMEMultipart()
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"Email sent successfully to {RECIPIENT_EMAIL}")
    except Exception as e:
        print(f"Error sending email: {e}")


class ChessHubHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def _send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/api/register":
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON payload"}, HTTPStatus.BAD_REQUEST)
            return

        required_fields = ["full_name", "whatsapp", "username", "payment_id"]
        missing = [field for field in required_fields if not str(payload.get(field, "")).strip()]

        if missing:
            self._send_json(
                {"error": f"Missing required fields: {', '.join(missing)}"},
                HTTPStatus.BAD_REQUEST,
            )
            return

        entry = {
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "full_name": str(payload.get("full_name", "")).strip(),
            "whatsapp": str(payload.get("whatsapp", "")).strip(),
            "username": str(payload.get("username", "")).strip(),
            "payment_id": str(payload.get("payment_id", "")).strip(),
            "note": str(payload.get("note", "")).strip(),
        }

        save_registration(entry)
        send_email_notification(entry)
        print(f"Saved registration: {entry}")
        self._send_json({"ok": True, "message": "Registration saved", "entry": entry})


if __name__ == "__main__":
    ensure_storage()
    server = ThreadingHTTPServer((HOST, PORT), ChessHubHandler)
    print(f"ChessHub server running at http://{HOST}:{PORT}")
    print(f"Registrations will be saved to {JSON_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
