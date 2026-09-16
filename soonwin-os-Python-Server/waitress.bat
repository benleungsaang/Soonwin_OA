@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
python -m waitress --host=0.0.0.0 --port=5000 wsgi:application
pause