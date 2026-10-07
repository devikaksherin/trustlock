import os

# MVP heuristic weights. Calibrate on real validation data before any production use.

CONFIG_VERSION = "mvp-heuristic-1"

WEIGHTS = {
    "identity": 0.25,
    "context": 0.25,
    "behavior": 0.20,
    "transaction": 0.30
}

THRESHOLDS = {
    "allow_min": 70,
    "verify_min": 40
}

HIGH_VALUE_INR = 100000

CONVERGENCE_MIN_CATEGORIES = 3
CONVERGENCE_SUBRISK = 50
CONVERGENCE_BONUS = 8
MEDIA_RISK_CAP = 25

DATA_DIR = os.environ.get("TRUSTLOCK_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
DB_PATH = os.path.join(DATA_DIR, "trustlock.db")

UPLOAD_LIMITS_MB = {"image": 15, "audio": 30, "document": 20, "video": 100}

ALLOWED_TYPES = {
    "image": ["jpg", "png", "webp"],
    "video": ["mp4", "webm", "mov"],
    "audio": ["wav", "mp3", "m4a", "ogg"],
    "document": ["pdf", "docx", "txt"]
}

EDITING_SOFTWARE = ["photoshop", "gimp", "canva", "illustrator", "inkscape", "pixlr", "affinity", "snapseed", "lightroom"]

ELA_MEAN_THRESHOLD = 4.0

MEDIA_HINTS = {
    "editing_software": 10,
    "ela_high": 8,
    "pdf_date_mismatch": 8,
    "name_not_in_document": 10
}

CHALLENGE_TTL_SECONDS = 90
CHALLENGE_MAX_ATTEMPTS = 3
CHALLENGE_VERIFY_SIMILARITY = 0.85
CHALLENGE_RETRY_SIMILARITY = 0.5
NONCE_WORDS = ["TRUST", "LOCK", "VERIFY", "SAFE", "ALPHA"]
