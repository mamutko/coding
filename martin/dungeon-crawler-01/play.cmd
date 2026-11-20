@echo off
rem Play the game locally with sound: serves this folder over http://localhost and opens it in the browser.
rem (Opened straight from disk, file://, the browser blocks fetch() of the music and voice clips; see README.)
rem Close the "Crypt server" window to stop the server.
cd /d "%~dp0"
set PORT=8137
set PY=python
where python >nul 2>nul || set PY=py
where %PY% >nul 2>nul || (echo Python was not found: install it from python.org, or open index.html directly ^(no music^). & pause & exit /b 1)
start "Crypt server" /min %PY% -m http.server %PORT% --bind 127.0.0.1
timeout /t 1 /nobreak >nul
start "" http://localhost:%PORT%/index.html
