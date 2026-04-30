@echo off
setlocal

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.10+ manually or via Windows Store.
    pause
    exit /b 1
)

echo [INFO] Python found.

:: Create Virtual Environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
) else (
    echo [INFO] Virtual environment already exists.
)

:: Activate Virtual Environment
call venv\Scripts\activate.bat

:: Install Requirements
if exist "requirements.txt" (
    echo [INFO] Installing requirements...
    pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo [WARNING] requirements.txt not found! Skipping dependency installation.
)

:: Java Installation Menu
:JAVA_MENU
echo.
echo ==========================================
echo         Java Installation Setup
echo ==========================================
echo [1] Install Java 8 (for older Minecraft versions 1.12.2 and below)
echo [2] Install Java 17 (for Minecraft 1.18 - 1.20.4)
echo [3] Install Java 21 (for Minecraft 1.20.5+)
echo [4] Install ALL Supported Java Versions (8, 17, 21)
echo [5] List Installed Java Versions
echo [6] Check current "java -version"
echo [7] Skip Java installation
echo ==========================================
set /p java_choice="Select an option (1-7): "

if "%java_choice%"=="1" goto INSTALL_JAVA8
if "%java_choice%"=="2" goto INSTALL_JAVA17
if "%java_choice%"=="3" goto INSTALL_JAVA21
if "%java_choice%"=="4" goto INSTALL_ALL
if "%java_choice%"=="5" goto LIST_JAVA
if "%java_choice%"=="6" goto CHECK_JAVA
if "%java_choice%"=="7" goto END

goto JAVA_MENU

:INSTALL_JAVA8
echo [INFO] Installing Java 8 (Eclipse Adoptium)...
winget install -e --id EclipseAdoptium.Temurin.8.JRE --silent --accept-package-agreements --accept-source-agreements
echo [INFO] Installation command sent.
goto JAVA_MENU

:INSTALL_JAVA17
echo [INFO] Installing Java 17 (Eclipse Adoptium)...
winget install -e --id EclipseAdoptium.Temurin.17.JRE --silent --accept-package-agreements --accept-source-agreements
echo [INFO] Installation command sent.
goto JAVA_MENU

:INSTALL_JAVA21
echo [INFO] Installing Java 21 (Eclipse Adoptium)...
winget install -e --id EclipseAdoptium.Temurin.21.JRE --silent --accept-package-agreements --accept-source-agreements
echo [INFO] Installation command sent.
goto JAVA_MENU

:INSTALL_ALL
echo [INFO] Installing ALL supported Java versions...
echo [INFO] Step 1/3: Installing Java 8...
winget install -e --id EclipseAdoptium.Temurin.8.JRE --silent --accept-package-agreements --accept-source-agreements
echo [INFO] Step 2/3: Installing Java 17...
winget install -e --id EclipseAdoptium.Temurin.17.JRE --silent --accept-package-agreements --accept-source-agreements
echo [INFO] Step 3/3: Installing Java 21...
winget install -e --id EclipseAdoptium.Temurin.21.JRE --silent --accept-package-agreements --accept-source-agreements
echo [INFO] All installations requested.
goto JAVA_MENU

:LIST_JAVA
echo.
echo [INFO] Listing installed Java versions (via Winget)...
winget list "Java"
echo.
echo [INFO] Checking Registry (Uninstall key)...
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /s /f "Java" 2>nul | findstr "DisplayName"
echo.
pause
goto JAVA_MENU

:CHECK_JAVA
echo.
java -version
echo.
pause
goto JAVA_MENU

:END
echo [INFO] Setup complete.
pause
