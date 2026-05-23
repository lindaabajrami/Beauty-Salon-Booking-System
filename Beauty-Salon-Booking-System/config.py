from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

APP_NAME = "Bloom Beauty Salon Booking System"
API_VERSION = "1.0.0"
API_PREFIX = "/api"

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000/api")
SALON_API_KEY = os.getenv("SALON_API_KEY", "salon-admin-key")

SEEDED_ADMIN_USERNAME = os.getenv("SEEDED_ADMIN_USERNAME", "admin")
SEEDED_ADMIN_PASSWORD = os.getenv("SEEDED_ADMIN_PASSWORD", "admin123")
SEEDED_USER_EMAIL = os.getenv("SEEDED_USER_EMAIL", "mira@example.com")
SEEDED_USER_PASSWORD = os.getenv("SEEDED_USER_PASSWORD", "student123")

DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "salon.db"
ASSETS_DIR = BASE_DIR / "assets"
SERVICE_IMAGE_DIR = ASSETS_DIR / "services"
