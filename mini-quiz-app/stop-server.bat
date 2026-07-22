@echo off
echo Stopping QuizSpark dev server...
taskkill /f /im node.exe /fi "WINDOWTITLE eq *http-server*" 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING') do (
  echo Killing PID %%a on port 8080
  taskkill /f /pid %%a 2>nul
)
echo Done.
timeout /t 2 >nul
