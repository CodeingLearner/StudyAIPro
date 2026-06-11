# StudyAI Pro

StudyAI Pro is a simple AI-powered academic assistant built with FastAPI and a frontend HTML/CSS template.

Features:
- User registration and JWT login
- Chat endpoint with streaming responses from Gemini API
- Mode selector (Doubt Solver, Summarizer, Quiz Generator)
- PDF upload and text extraction via PyPDF2
- SQLite for chat history

Environment variables:
- `GEMINI_API_KEY` — API key for Gemini
- `GEMINI_API_URL` — (optional) override streaming endpoint
- `STUDYAI_SECRET_KEY` — JWT secret (optional; default used if unset)

Use a `.env` file for local development (do NOT commit it). A `.env.example` is provided — copy it to `.env` and fill in your real keys.

To load variables from `.env` automatically during development, install `python-dotenv` (already added to `requirements.txt`) and ensure your app loads it, or set env vars in your shell before running the server.

Run locally:

1. Create a venv and install requirements:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Set environment variables (PowerShell):

```powershell
$env:GEMINI_API_KEY = 'your_key'
$env:STUDYAI_SECRET_KEY = 'a_secret'
```

3. Start the server:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Notes:
- `services/ai_service.py` contains a streaming client for a Gemini-like API. Adjust `GEMINI_API_URL` and payload format to match the real API.
- The frontend in `templates/index.html` is a minimal, dark UI that demonstrates registration, login, PDF upload and streaming chat.
