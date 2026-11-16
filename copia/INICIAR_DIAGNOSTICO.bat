@echo off
cd /d "%~dp0"
"C:\Users\Antonio Garcia\AppData\Local\Programs\Python\Python315\python.exe" modmenu.py > log_error.txt 2>&1
echo Si hubo un error, se guardo en log_error.txt
type log_error.txt 2>nul
pause
