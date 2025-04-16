@echo off
REM Get the directory where the script is located
set SCRIPT_DIR=%~dp0

REM Set PYTHONPATH to include the src directory
set PYTHONPATH=%SCRIPT_DIR%src;%PYTHONPATH%

REM Launch the Python GUI application without waiting and close this console
REM The "" is a required placeholder for the window title for the 'start' command.
start "" python src/app.py

REM Exit the batch script immediately
exit /b 