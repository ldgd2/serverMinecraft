@echo off
SETLOCAL EnableDelayedExpansion

REM Minecraft Server Manager - Windows Installer

echo Detection of Operating System: Windows
echo.

REM Check for Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Check for Java (Simple check)
java -version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Java is not installed. 
    echo Attempting to install OpenJDK using Winget...
    winget install -e --id Microsoft.OpenJDK.17
    IF %ERRORLEVEL% NEQ 0 (
        echo Failed to install Java automatically. Please install Java 17 manually.
        pause
    )
) ELSE (
    echo Java is detected.
)

REM Create Virtual Environment
IF NOT EXIST "venv" (
    echo Creating Python Virtual Environment...
    python -m venv venv
) ELSE (
    echo Virtual Environment already exists.
)

REM Activate Venv and Install Dependencies
echo Installing Dependencies...
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Run Main Setup Script
echo Running Setup Configuration...
python setup.py

echo.
echo Installation Complete!
echo You can now run the server using: 
echo venv\Scripts\python run.py
echo.
pause
