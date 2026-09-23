import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

if os.getenv('VERCEL'):
	DB_PATH = Path('/tmp/green_chemistry.db')
else:
	DB_PATH = BASE_DIR / 'database' / 'green_chemistry.db'
DATA_DIR = BASE_DIR / 'data'
SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_hex(32)
AI_API_KEY = os.getenv('AI_API_KEY', '').strip()
AI_API_URL = os.getenv('AI_API_URL', '').strip()
AI_MODEL = os.getenv('AI_MODEL', '').strip()
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin').strip()
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '').strip()
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@greenlab.local').strip()
