@echo off
setlocal

set "BASE_DIR=%CD%"
set "HOST_URL="

:parse_args
if "%~1"=="" goto configure

if /I "%~1"=="-b" goto base_dir
if /I "%~1"=="--base-dir" goto base_dir
if /I "%~1"=="--host" goto host_name
if /I "%~1"=="-h" goto help
if /I "%~1"=="--help" goto help

echo Error: unknown option: %~1 >&2
echo Usage: %~nx0 [-b ^| --base-dir DIR] [--host HOSTNAME] >&2
exit /b 1

:base_dir
if "%~2"=="" (
    echo Error: %~1 requires a directory argument. >&2
    exit /b 1
)

set "BASE_DIR=%~2"
shift
shift
goto parse_args

:host_name
if "%~2"=="" (
    echo Error: %~1 requires a hostname argument. >&2
    exit /b 1
)

set "HOST_URL=%~2"
shift
shift
goto parse_args

:configure
for %%I in ("%BASE_DIR%") do set "BASE_DIR=%%~fI"

if not exist "%BASE_DIR%\" (
    echo "%BASE_DIR%" is not a directory. >&2
    exit /b 1
)

set "BASE_DIR=%BASE_DIR:\=\\%"

if defined HOST_URL (
    echo %HOST_URL% | findstr /r /i /b /c:"http://" /c:"https://" >nul
    if errorlevel 1 (
        echo Not a HTTP[S] hostname: "%HOST_URL%" >&2
        exit /b 1
    )
)

set "LABEL_STUDIO_BASE_DATA_DIR=%BASE_DIR%\\label-studio\\app"
set "LABEL_STUDIO_PORT=8080"
set "LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true"
set "LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=%BASE_DIR%\\label-studio\\local_store"

echo Label Studio environment configured:
echo   LABEL_STUDIO_BASE_DATA_DIR=%LABEL_STUDIO_BASE_DATA_DIR%
echo   LABEL_STUDIO_PORT=%LABEL_STUDIO_PORT%
echo   LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=%LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED%
echo   LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=%LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT%

if defined HOST_URL (
    echo   LABEL_STUDIO_HOST=%HOST_URL%
    echo   CSRF_TRUSTED_ORIGINS=%HOST_URL%
)

endlocal & (
    set "LABEL_STUDIO_BASE_DATA_DIR=%LABEL_STUDIO_BASE_DATA_DIR%"
    set "LABEL_STUDIO_PORT=%LABEL_STUDIO_PORT%"
    set "LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=%LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED%"
    set "LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=%LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT%"
    set "LABEL_STUDIO_HOST=%HOST_URL%"
    set "CSRF_TRUSTED_ORIGINS=%HOST_URL%"
)
exit /b 0

:help
echo Usage: %~nx0 [-b ^| --base-dir DIR] [--host HOSTNAME]
exit /b 0
