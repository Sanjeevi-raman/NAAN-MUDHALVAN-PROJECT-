@echo off
echo Starting PocketSmart AI...
echo Opening in your browser at http://127.0.0.1:8000
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
