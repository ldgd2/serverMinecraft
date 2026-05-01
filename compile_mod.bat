@echo off
setlocal EnableDelayedExpansion
echo ====================================================
echo   MINEBRIDGE VIRTUAL BUILD ENV (ISOLATED)
echo ====================================================
echo.

set "MOD_DIR=%~dp0mod"
set "LOCAL_JDK=%MOD_DIR%\.jdk21"
set "LOCAL_GRADLE=%MOD_DIR%\.gradle_home"

cd /d "%MOD_DIR%"

:: 1. Descargar JDK 21 Portable si no existe
if exist "%LOCAL_JDK%" goto :jdk_exists

echo [INFO] Creando entorno virtual de Java 21...
echo [INFO] Descargando JDK 21 Portable (Temurin)...
echo [INFO] Esto puede tardar un poco...

:: Usamos una variable para la URL para evitar problemas con %
set "JDK_URL=https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.4+7/OpenJDK21U-jdk_x64_windows_hotspot_21.0.4_7.zip"

powershell -Command "$ErrorActionPreference = 'Stop'; New-Item -ItemType Directory -Force -Path '%LOCAL_JDK%'; Write-Host 'Conectando con el servidor...'; iwr '%JDK_URL%' -OutFile jdk21.zip; Write-Host 'Extrayendo...'; Expand-Archive jdk21.zip -DestinationPath '%LOCAL_JDK%'; Remove-Item jdk21.zip"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] No se pudo crear el entorno virtual. Revisa tu conexion.
    pause
    exit /b 1
)

:jdk_exists
echo [OK] Java 21 aislado detectado.

:: Configurar variables de sesion (SOLO para esta ventana)
for /d %%i in ("%LOCAL_JDK%\jdk*") do set "JAVA_HOME=%%i"
set "PATH=!JAVA_HOME!\bin;%PATH%"
set "GRADLE_USER_HOME=%LOCAL_GRADLE%"

echo [INFO] Java Home: %JAVA_HOME%
echo [INFO] Gradle Home: %GRADLE_USER_HOME%
echo.

:: 2. Setup de Gradle Wrapper si no existe
if exist "gradlew.bat" goto :gradle_exists
echo [INFO] Configurando Gradle estable...
powershell -Command "New-Item -ItemType Directory -Force -Path 'gradle/wrapper'; iwr https://github.com/gradle/gradle/raw/v8.10.0/gradlew.bat -OutFile gradlew.bat; iwr https://github.com/gradle/gradle/raw/v8.10.0/gradle/wrapper/gradle-wrapper.jar -OutFile gradle/wrapper/gradle-wrapper.jar; "

:gradle_exists

echo [INFO] Verificando entorno...
java -version
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No se pudo ejecutar Java. Borra la carpeta .jdk21 e intenta de nuevo.
    pause
    exit /b 1
)

echo.
echo [INFO] Compilando mod en entorno aislado...
call gradlew.bat clean build

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   COMPILACION EXITOSA!
    echo ========================================
    echo Tu mod esta en: %MOD_DIR%\build\libs\minebridge-1.0.0.jar
) else (
    echo.
    echo [ERROR] La compilacion fallo.
)

pause
