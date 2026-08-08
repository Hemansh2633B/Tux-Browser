@echo off
REM Tux Browser Installer for Windows (Batch version)
REM Usage: install_windows.bat [--clean] [--fetch-chromium] [--build] [--fetch-and-build] [--user] [--uninstall] [--help]

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set CHROMIUM_SRC=%SCRIPT_DIR%..\chromium-main\chromium-main
set BUILD_DIR=%CHROMIUM_SRC%\out\tux_browser
set BINARY=%BUILD_DIR%\chrome.exe

set PREFIX=%ProgramFiles%\Tux Browser
set USER_INSTALL=0
set FETCH_CHROMIUM=0
set BUILD=0
set FETCH_AND_BUILD=0
set UNINSTALL=0
set CLEAN=0
set HELP=0

REM Parse arguments
:PARSE_ARGS
if "%~1"=="" goto PARSE_DONE
if "%~1"=="--help" set HELP=1 & shift & goto PARSE_ARGS
if "%~1"=="-h" set HELP=1 & shift & goto PARSE_ARGS
if "%~1"=="--clean" set CLEAN=1 & shift & goto PARSE_ARGS
if "%~1"=="--fetch-chromium" set FETCH_CHROMIUM=1 & shift & goto PARSE_ARGS
if "%~1"=="--build" set BUILD=1 & shift & goto PARSE_ARGS
if "%~1"=="--fetch-and-build" set FETCH_AND_BUILD=1 & shift & goto PARSE_ARGS
if "%~1"=="--user" set USER_INSTALL=1 & shift & goto PARSE_ARGS
if "%~1"=="--uninstall" set UNINSTALL=1 & shift & goto PARSE_ARGS
shift
goto PARSE_ARGS

:PARSE_DONE

if %HELP%==1 goto SHOW_HELP

if %FETCH_AND_BUILD%==1 (
    set FETCH_CHROMIUM=1
    set BUILD=1
)

if %UNINSTALL%==1 goto DO_UNINSTALL

REM Fetch Chromium if requested
if %FETCH_CHROMIUM%==1 (
    echo Fetching Chromium source...
    
    REM Check if depot_tools is available
    set DEPOT_TOOLS_DIR=%USERPROFILE%\.tux-browser\depot_tools
    if not exist "%DEPOT_TOOLS_DIR%\gclient" (
        echo Installing depot_tools...
        if not exist "%DEPOT_TOOLS_DIR%" (
            git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git "%DEPOT_TOOLS_DIR%"
        )
        set PATH=%DEPOT_TOOLS_DIR%;%PATH%
    )
    
    REM Create chromium-main directory
    set CHROMIUM_MAIN_DIR=%SCRIPT_DIR%..\chromium-main
    if not exist "%CHROMIUM_MAIN_DIR%" mkdir "%CHROMIUM_MAIN_DIR%"
    cd /d "%CHROMIUM_MAIN_DIR%"
    
    REM Initialize gclient if needed
    if not exist ".gclient" (
        echo Configuring gclient for Chromium...
        (
            echo solutions = [
            echo   {
            echo     "name": "chromium-main",
            echo     "url": "https://chromium.googlesource.com/chromium/src.git",
            echo     "deps_file": "DEPS",
            echo     "managed": True,
            echo     "custom_deps": {},
            echo     "safesync_url": "",
            echo   },
            echo ]
            echo target_os = ["win"]
            echo target_os_only = True
        ) > .gclient
    )
    
    REM Sync Chromium
    echo Syncing Chromium source (this may take 30-60 minutes)...
    gclient sync --no-history --shallow
    
    echo Chromium source fetched successfully
)

REM Build if requested
if %BUILD%==1 (
    echo Building Tux Browser...
    
    if not exist "%CHROMIUM_SRC%\BUILD.gn" (
        echo ERROR: Chromium source not found. Run with --fetch-chromium first.
        exit /b 1
    )
    
    cd /d "%CHROMIUM_SRC%"
    call ..\..\build_tux_browser.bat --clean
    
    echo Tux Browser built successfully
)

if %USER_INSTALL%==1 (
    set PREFIX=%LOCALAPPDATA%\Tux Browser
)

:DO_INSTALL
echo ==========================================
echo Tux Browser Installer for Windows
echo ==========================================
echo Installing to: %PREFIX%
echo.

REM Check if build exists
if not exist "%BINARY%" (
    echo ERROR: Tux Browser binary not found at %BINARY%
    echo Run with --fetch-and-build to fetch Chromium and build, or build first: .\build_tux_browser.bat
    exit /b 1
)

REM Create directories
set BIN_DIR=%PREFIX%\bin
set LIB_DIR=%PREFIX%\lib
set TOR_DIR=%PREFIX%\tor
set PT_DIR=%TOR_DIR%\pluggable_transports

if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
if not exist "%LIB_DIR%" mkdir "%LIB_DIR%"
if not exist "%TOR_DIR%" mkdir "%TOR_DIR%"
if not exist "%PT_DIR%" mkdir "%PT_DIR%"

REM Copy browser binary
echo Copying browser binary...
copy /y "%BINARY%" "%LIB_DIR%\tux-browser.exe" >nul
echo Installed to %LIB_DIR%\tux-browser.exe

REM Copy Tor if available
set TOR_SOURCE=%SCRIPT_DIR%..\tor-expert-bundle-windows-x64\tor
if exist "%TOR_SOURCE%\tor.exe" (
    echo Copying embedded Tor...
    copy /y "%TOR_SOURCE%\tor.exe" "%TOR_DIR%\tor.exe" >nul
    copy /y "%TOR_SOURCE%\libcrypto-3-x64.dll" "%TOR_DIR%\libcrypto-3-x64.dll" >nul 2>nul
    copy /y "%TOR_SOURCE%\libssl-3-x64.dll" "%TOR_DIR%\libssl-3-x64.dll" >nul 2>nul
    copy /y "%TOR_SOURCE%\libevent-2.1-7.dll" "%TOR_DIR%\libevent-2.1-7.dll" >nul 2>nul
    
    REM Copy pluggable transports
    if exist "%TOR_SOURCE%\pluggable_transports\" (
        copy /y "%TOR_SOURCE%\pluggable_transports\*.exe" "%PT_DIR%\" >nul
        echo Installed pluggable transports
    )
    echo Installed embedded Tor
) else (
    echo WARNING: Embedded Tor not found at %TOR_SOURCE%
    echo You'll need to install Tor separately from https://torproject.org
)

REM Create launcher scripts
echo Creating launchers...

REM Batch launcher
(
    echo @echo off
    echo REM Tux Browser Launcher for Windows
    echo.
    echo set INSTALL_DIR=%%~dp0..
    echo set LIB_DIR=%%INSTALL_DIR%%\lib
    echo set TOR_DIR=%%INSTALL_DIR%%\tor
    echo set TOR_DATA_DIR=%%LOCALAPPDATA%%\Tux Browser\tor
    echo set PROFILE_DIR=%%LOCALAPPDATA%%\Tux Browser\profile
    echo.
    echo mkdir "%%TOR_DATA_DIR%%" 2^>nul
    echo mkdir "%%PROFILE_DIR%%" 2^>nul
    echo.
    echo REM Check if Tor is running
    echo netstat -an | findstr ":9050" ^>nul 2^>nul
    echo if errorlevel 1 (
    echo     REM Try to start embedded Tor
    echo     if exist "%%TOR_DIR%%\tor.exe" (
    echo         start /b "" "%%TOR_DIR%%\tor.exe" --DataDirectory "%%TOR_DATA_DIR%%" --SOCKSPort 9050 --ControlPort 9051 --CookieAuthentication 1 --Log notice stdout --AvoidDiskWrites 1
    echo.
    echo         REM Wait for Tor to start
    echo         for /l %%%%i in (1,1,30) do (
    echo             timeout /t 1 /nobreak ^>nul
    echo             netstat -an | findstr ":9050" ^>nul 2^>nul
    echo             if not errorlevel 1 goto TOR_STARTED
    echo         )
    echo         echo WARNING: Tor failed to start within 30 seconds
    echo     ) else (
    echo         echo WARNING: Embedded Tor not found. Please install Tor from https://torproject.org
    echo         echo          and ensure it's running on localhost:9050
    echo     )
    echo )
    echo.
    echo :TOR_STARTED
    echo.
    echo REM Launch browser
    echo "%%LIB_DIR%%\tux-browser.exe" --enable-features=TorNetworking --proxy-server=socks5h://127.0.0.1:9050 --user-data-dir="%%PROFILE_DIR%%" %%*
) > "%BIN_DIR%\tux-browser.bat"

REM PowerShell launcher
(
    echo # Tux Browser Launcher for Windows (PowerShell)
    echo.
    echo $InstallDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    echo $LibDir = Join-Path $InstallDir '..\lib'
    echo $TorDir = Join-Path $InstallDir '..\tor'
    echo $TorDataDir = Join-Path $env:LOCALAPPDATA 'Tux Browser\tor'
    echo $ProfileDir = Join-Path $env:LOCALAPPDATA 'Tux Browser\profile'
    echo.
    echo New-Item -ItemType Directory -Force -Path $TorDataDir, $ProfileDir | Out-Null
    echo.
    echo # Check if Tor is running
    echo $torRunning = Get-NetTCPConnection -LocalPort 9050 -State Listen -ErrorAction SilentlyContinue
    echo if (-not $torRunning) {
    echo     # Try to start embedded Tor
    echo     $torExe = Join-Path $TorDir 'tor.exe'
    echo     if (Test-Path $torExe) {
    echo         $torProcess = Start-Process -FilePath $torExe -ArgumentList '--DataDirectory', $TorDataDir, '--SOCKSPort', '9050', '--ControlPort', '9051', '--CookieAuthentication', '1', '--Log', 'notice stdout', '--AvoidDiskWrites', '1' -WindowStyle Hidden -PassThru
    echo.
    echo         # Wait for Tor to start
    echo         for ($i = 0; $i -lt 30; $i++) {
    echo             Start-Sleep -Seconds 1
    echo             $torRunning = Get-NetTCPConnection -LocalPort 9050 -State Listen -ErrorAction SilentlyContinue
    echo             if ($torRunning) { break }
    echo         }
    echo         if (-not $torRunning) {
    echo             Write-Warning 'Tor failed to start within 30 seconds'
    echo         }
    echo     } else {
    echo         Write-Warning 'Embedded Tor not found. Please install Tor from https://torproject.org'
    echo         Write-Warning 'and ensure it'"'"'s running on localhost:9050'
    echo     }
    echo }
    echo.
    echo # Launch browser
    echo $browserExe = Join-Path $LibDir 'tux-browser.exe'
    echo $args = @('--enable-features=TorNetworking', '--proxy-server=socks5h://127.0.0.1:9050', '--user-data-dir=' + $ProfileDir) + $args
    echo Start-Process -FilePath $browserExe -ArgumentList $args
) > "%BIN_DIR%\tux-browser.ps1"

echo Created launchers

REM Create Start Menu shortcut (requires PowerShell)
powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; ^
    $StartMenu = $WshShell.SpecialFolders('StartMenu'); ^
    $ShortcutPath = Join-Path $StartMenu 'Programs\Tux Browser.lnk'; ^
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath); ^
    $Shortcut.TargetPath = '%BIN_DIR%\tux-browser.ps1'; ^
    $Shortcut.WorkingDirectory = '%BIN_DIR%'; ^
    $Shortcut.Description = 'Tux Browser - Privacy-focused browser with integrated Tor'; ^
    $Shortcut.IconLocation = '%LIB_DIR%\tux-browser.exe,0'; ^
    $Shortcut.Save(); ^
    Write-Host 'Created Start Menu shortcut'"

REM Create Desktop shortcut
powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; ^
    $Desktop = $WshShell.SpecialFolders('Desktop'); ^
    $ShortcutPath = Join-Path $Desktop 'Tux Browser.lnk'; ^
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath); ^
    $Shortcut.TargetPath = '%BIN_DIR%\tux-browser.ps1'; ^
    $Shortcut.WorkingDirectory = '%BIN_DIR%'; ^
    $Shortcut.Description = 'Tux Browser - Privacy-focused browser with integrated Tor'; ^
    $Shortcut.IconLocation = '%LIB_DIR%\tux-browser.exe,0'; ^
    $Shortcut.Save(); ^
    Write-Host 'Created Desktop shortcut'"

REM Add to PATH (user)
set USER_PATH=%PATH%
if not "!USER_PATH:%BIN_DIR%=!"=="%USER_PATH%" (
    setx PATH "%USER_PATH%;%BIN_DIR%"
    echo Added to user PATH
)

echo.
echo ==========================================
echo Installation complete!
echo ==========================================
echo.
echo You can now run Tux Browser from:
echo   - Start Menu: Tux Browser
echo   - Desktop shortcut: Tux Browser
echo   - Command prompt: tux-browser
echo   - PowerShell: tux-browser
echo.
echo On first launch, Tux Browser will connect to Tor network (10-30 seconds).
echo Visit https://check.torproject.org to verify your connection.
goto END

:DO_UNINSTALL
echo Uninstalling Tux Browser...

set LOCATIONS="%ProgramFiles%\Tux Browser" "%LOCALAPPDATA%\Tux Browser" "%ProgramFiles(x86)%\Tux Browser"
for %%L in (%LOCATIONS%) do (
    if exist "%%L" (
        rmdir /s /q "%%L" 2>nul
        echo Removed %%L
    )
)

REM Remove shortcuts
set SHORTCUTS="%ProgramData%\Microsoft\Windows\Start Menu\Programs\Tux Browser.lnk" "%AppData%\Microsoft\Windows\Start Menu\Programs\Tux Browser.lnk" "%Public%\Desktop\Tux Browser.lnk" "%UserProfile%\Desktop\Tux Browser.lnk"
for %%S in (%SHORTCUTS%) do (
    if exist "%%S" (
        del /f /q "%%S" 2>nul
        echo Removed shortcut: %%S
    )
)

REM Remove from PATH
set USER_PATH=%PATH%
if "!USER_PATH:%BIN_DIR%=!" NEQ "%USER_PATH%" (
    set NEW_PATH=!USER_PATH:%BIN_DIR%;=!
    set NEW_PATH=!NEW_PATH:%BIN_DIR%=!
    setx PATH "!NEW_PATH!"
    echo Removed from user PATH
)

echo Uninstallation complete!
goto END

:SHOW_HELP
echo Tux Browser Installer for Windows
echo.
echo Usage: install_windows.bat [options]
echo Options:
echo   --clean              Clean build directory before building
echo   --fetch-chromium     Fetch Chromium source before building
echo   --build              Build Tux Browser after fetching
echo   --fetch-and-build    Fetch Chromium and build (full setup)
echo   --user               Install to %%LOCALAPPDATA%%\Tux Browser
echo   --uninstall          Uninstall Tux Browser
echo   --help               Show this help
echo.
echo Examples:
echo   install_windows.bat --fetch-and-build
echo   install_windows.bat --user --fetch-and-build
echo   install_windows.bat --uninstall

:END