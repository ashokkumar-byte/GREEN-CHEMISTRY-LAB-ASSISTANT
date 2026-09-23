import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

DB_PATH = BASE_DIR / 'database' / 'green_chemistry.db'
DATA_DIR = BASE_DIR / 'data'
SECRET_KEY = os.getenv('SECRET_KEY', 'green-chemistry-dev-key-change-me')
AI_API_KEY = os.getenv('AI_API_KEY', '').strip()
AI_API_URL = os.getenv('AI_API_URL', '').strip()
AI_MODEL = os.getenv('AI_MODEL', '').strip()
