@echo off
title YouTube MP3 Downloader
chcp 65001 > nul
setlocal enabledelayedexpansion

REM =========================================
REM CONFIG
REM =========================================

set LINKS=links.txt
set PASTA=downloads

REM =========================================
REM CRIA PASTA
REM =========================================

if not exist "%PASTA%" mkdir "%PASTA%"

echo.
echo =========================================
echo        YOUTUBE MP3 DOWNLOADER
echo =========================================
echo.

REM =========================================
REM VERIFICA yt-dlp
REM =========================================

where yt-dlp >nul 2>nul
if errorlevel 1 (
    echo [ERRO] yt-dlp nao encontrado
    pause
    exit /b
)

REM =========================================
REM VERIFICA ffmpeg
REM =========================================

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo [ERRO] ffmpeg nao encontrado
    pause
    exit /b
)

REM =========================================
REM VERIFICA links.txt
REM =========================================

if not exist "%LINKS%" (
    echo [ERRO] Arquivo links.txt nao encontrado
    pause
    exit /b
)

REM =========================================
REM ATUALIZA yt-dlp
REM =========================================

echo Atualizando yt-dlp...
yt-dlp -U

echo.
echo Iniciando downloads...
echo.

REM =========================================
REM DOWNLOADS
REM =========================================

for /f "usebackq delims=" %%A in ("%LINKS%") do (

    if not "%%A"=="" (

        echo --------------------------------------------------
        echo URL:
        echo %%A
        echo --------------------------------------------------

        yt-dlp ^
            --newline ^
            --progress ^
            --console-title ^
            --ignore-errors ^
            --no-playlist ^
            --extract-audio ^
            --audio-format mp3 ^
            --audio-quality 0 ^
            --embed-thumbnail ^
            --convert-thumbnails jpg ^
            --embed-metadata ^
            --add-metadata ^
            --windows-filenames ^
            --parse-metadata "%%(title)s:%%(artist)s - %%(title)s" ^
            --retries 10 ^
            --fragment-retries 10 ^
            --concurrent-fragments 8 ^
            -o "%PASTA%\%%(artist)s - %%(title)s.%%(ext)s" ^
            "%%A"

        echo.
    )
)

echo =========================================
echo             FINALIZADO
echo =========================================
echo.

pause