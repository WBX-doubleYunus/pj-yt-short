@echo off
REM Run development server
set PYTHONPATH=%CD%
uvicorn app.main:app --reload --port 8000
