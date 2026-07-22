@echo off
echo Starting QuizSpark dev server on http://localhost:8080
echo Press Ctrl+C to stop
echo.
npx -y http-server -p 8080 -c-1 --cors
