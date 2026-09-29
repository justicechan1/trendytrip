@echo off
set PYTHONPATH=%CD%\TripScheduler
python -m uvicorn app.main:app --reload