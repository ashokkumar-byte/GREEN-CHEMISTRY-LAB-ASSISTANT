# Green Chemistry Lab Assistant

A Flask + HTML/CSS/JavaScript educational web application for green chemistry learning.

## Run
1. Install Python 3.10+.
2. Open this project folder in PowerShell or Command Prompt.
3. Run `start.bat`.
4. Open http://127.0.0.1:5000

## Configuration
Copy `.env.example` to `.env` for local configuration. Set `SECRET_KEY` and
`ADMIN_PASSWORD` through Vercel environment variables for deployment. AI
provider variables are optional; the assistant has an educational fallback.

The SQLite database is intentionally ignored by Git. Local runs store it in
`database/`; Vercel serverless instances use `/tmp`, which is ephemeral. Use a
managed database before relying on persistent production user activity.

## Vercel deployment
The existing Flask application is exposed through `api/index.py` and
`vercel.json`. Vercel serves the frontend and API from the same origin, so the
frontend's relative `/api` requests work without a separate CORS configuration.

The backend automatically creates the SQLite database in `database/green_chemistry.db` on first run. The included database file is only a placeholder so the requested structure is present.

## Main features
- Student registration and login
- Dashboard and profile
- Green chemistry experiments
- 12 principles
- Laboratory safety and waste management
- Safer alternatives
- Educational AI assistant fallback
- Quiz and activity history
- Admin UI starter pages

For real production deployment, add secure admin authentication, HTTPS, proper secret management, backups and an approved AI provider/API configuration.
