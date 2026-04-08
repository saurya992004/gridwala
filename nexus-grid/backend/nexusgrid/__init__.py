"""NEXUS GRID backend package bootstrap."""

from pathlib import Path

from dotenv import load_dotenv


PACKAGE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = PACKAGE_DIR.parent
WORKSPACE_DIR = BACKEND_DIR.parent.parent

# Load local secrets without committing them. Backend-local values win.
load_dotenv(WORKSPACE_DIR / ".env", override=False)
load_dotenv(BACKEND_DIR / ".env", override=False)
