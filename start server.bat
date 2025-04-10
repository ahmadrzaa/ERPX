@echo off
:: Start the Django development server
start cmd /k "python manage.py runserver 0.0.0.0:8000"

:: Wait for the server to start and run ngrok
timeout /t 5 >nul

:: Start ngrok to expose port 8000
start cmd /k "ngrok http 8000"

:: Keep the script window open (optional)
pause
