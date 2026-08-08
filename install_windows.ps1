<# 
.SYNOPSIS
    Tux Browser Installer for Windows

.DESCRIPTION
    Installs Tux Browser system-wide or user-wide on Windows

.PARAMETER Prefix
    Installation prefix (default: $env:ProgramFiles\Tux Browser)

.PARAMETER User
    Install to %LOCALAPPDATA%\Tux Browser instead of system-wide

.PARAMETER Uninstall
    Uninstall Tux Browser

.EXAMPLE
    .\install_windows.ps1

.EXAMPLE
    .\install_windows.ps1 -User

.EXAMPLE
    .\install_windows.ps1 -Uninstall
#>

param(
    [string]$Prefix = "$env:ProgramFiles\Tux Browser",
    [switch]$User,
    [switch]$Uninstall,
    [switch]$Help
)

if ($Help) {
    Write-Host "Tux Browser Installer for Windows" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\install_windows.ps1 [options]"
    Write-Host "Options:"
    Write-Host "  --Prefix=DIR       Installation directory (default: $env:ProgramFiles\Tux Browser)"
    Write-Host "  --User             Install to %LOCALAPPDATA%\Tux Browser"
    Write-Host "  --Uninstall        Uninstall Tux Browser"
    Write-Host "  --Help             Show this help"
    exit 0
}

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BuildDir = Join-Path $ScriptDir "chromium-main\chromium-main\out\tux_browser"
$Binary = Join-Path $BuildDir "chrome.exe"

function Uninstall-TuxBrowser {
    Write-Host "Uninstalling Tux Browser..." -ForegroundColor Yellow
    
    $locations = @(
        "$env:ProgramFiles\Tux Browser",
        "$env:LocalAppData\Tux Browser",
        "$env:ProgramFiles(x86)\Tux Browser"
    )
    
    foreach ($location in $locations) {
        if (Test-Path $location) {
            Remove-Item -Recurse -Force $location -ErrorAction SilentlyContinue
            Write-Host "Removed $location" -ForegroundColor Green
        }
    }
    
    # Remove shortcuts
    $shortcuts = @(
        "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Tux Browser.lnk",
        "$env:AppData\Microsoft\Windows\Start Menu\Programs\Tux Browser.lnk",
        "$env:Public\Desktop\Tux Browser.lnk",
        "$env:UserProfile\Desktop\Tux Browser.lnk"
    )
    
    foreach ($shortcut in $shortcuts) {
        if (Test-Path $shortcut) {
            Remove-Item -Force $shortcut -ErrorAction SilentlyContinue
            Write-Host "Removed shortcut: $shortcut" -ForegroundColor Green
        }
    }
    
    # Remove from PATH (user)
    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($userPath -like "*Tux Browser*") {
        $newPath = $userPath -split ';' | Where-Object { $_ -notlike "*Tux Browser*" } -join ';'
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
        Write-Host "Removed from user PATH" -ForegroundColor Green
    }
    
    Write-Host "Uninstallation complete!" -ForegroundColor Green
    exit 0
}

if ($Uninstall) {
    Uninstall-TuxBrowser
}

if ($User) {
    $Prefix = "$env:LocalAppData\Tux Browser"
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Tux Browser Installer for Windows" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installing to: $Prefix" -ForegroundColor Yellow
Write-Host ""

# Check if build exists
if (-not (Test-Path $Binary)) {
    Write-Error "ERROR: Tux Browser binary not found at $Binary"
    Write-Host "Please build first: .\build_tux_browser.ps1" -ForegroundColor Yellow
    exit 1
}

# Create directories
$BinDir = Join-Path $Prefix "bin"
$LibDir = Join-Path $Prefix "lib"
$TorDir = Join-Path $Prefix "tor"
$PTDir = Join-Path $TorDir "pluggable_transports"

New-Item -ItemType Directory -Force -Path $BinDir, $LibDir, $TorDir, $PTDir | Out-Null

# Copy browser binary
Write-Host "Copying browser binary..." -ForegroundColor Yellow
Copy-Item $Binary -Destination (Join-Path $LibDir "tux-browser.exe") -Force
Write-Host "Installed to $LibDir\tux-browser.exe" -ForegroundColor Green

# Copy Tor if available
$TorSource = Join-Path $ScriptDir "tor-expert-bundle-linux-x86_64-15.0.19\tor"
if (Test-Path (Join-Path $TorSource "tor.exe")) {
    Write-Host "Copying embedded Tor..." -ForegroundColor Yellow
    Copy-Item (Join-Path $TorSource "tor.exe") -Destination (Join-Path $TorDir "tor.exe") -Force
    Copy-Item (Join-Path $TorSource "libcrypto-3-x64.dll") -Destination (Join-Path $TorDir "libcrypto-3-x64.dll") -Force -ErrorAction SilentlyContinue
    Copy-Item (Join-Path $TorSource "libssl-3-x64.dll") -Destination (Join-Path $TorDir "libssl-3-x64.dll") -Force -ErrorAction SilentlyContinue
    Copy-Item (Join-Path $TorSource "libevent-2.1-7.dll") -Destination (Join-Path $TorDir "libevent-2.1-7.dll") -Force -ErrorAction SilentlyContinue
    
    # Copy pluggable transports
    $PTSource = Join-Path $TorSource "pluggable_transports"
    if (Test-Path $PTSource) {
        Get-ChildItem $PTSource | Where-Object { $_.Extension -eq '.exe' } | ForEach-Object {
            Copy-Item $_.FullName -Destination (Join-Path $PTDir $_.Name) -Force
        }
        Write-Host "Installed pluggable transports" -ForegroundColor Green
    }
    Write-Host "Installed embedded Tor" -ForegroundColor Green
} else {
    Write-Host "WARNING: Embedded Tor not found at $TorSource" -ForegroundColor Yellow
    Write-Host "You'll need to install Tor separately from https://torproject.org" -ForegroundColor Yellow
}

# Create launcher script
$Launcher = @"
@echo off
REM Tux Browser Launcher for Windows

set INSTALL_DIR=%~dp0..
set LIB_DIR=%INSTALL_DIR%\lib
set TOR_DIR=%INSTALL_DIR%\tor
set TOR_DATA_DIR=%LOCALAPPDATA%\Tux Browser\tor
set PROFILE_DIR=%LOCALAPPDATA%\Tux Browser\profile

mkdir "%TOR_DATA_DIR%" 2>nul
mkdir "%PROFILE_DIR%" 2>nul

REM Check if Tor is running
netstat -an | findstr ":9050" >nul 2>nul
if errorlevel 1 (
    REM Try to start embedded Tor
    if exist "%TOR_DIR%\tor.exe" (
        start /b "" "%TOR_DIR%\tor.exe" --DataDirectory "%TOR_DATA_DIR%" --SOCKSPort 9050 --ControlPort 9051 --CookieAuthentication 1 --Log notice stdout --AvoidDiskWrites 1
        
        REM Wait for Tor to start
        for /l %%i in (1,1,30) do (
            timeout /t 1 /nobreak >nul
            netstat -an | findstr ":9050" >nul 2>nul
            if not errorlevel 1 goto TOR_STARTED
        )
        echo WARNING: Tor failed to start within 30 seconds
    ) else (
        echo WARNING: Embedded Tor not found. Please install Tor from https://torproject.org
        echo          and ensure it's running on localhost:9050
    )
)

:TOR_STARTED

REM Launch browser
"%LIB_DIR%\tux-browser.exe" --enable-features=TorNetworking --proxy-server=socks5h://127.0.0.1:9050 --user-data-dir="%PROFILE_DIR%" %*
"@

$LauncherPath = Join-Path $BinDir "tux-browser.bat"
$Launcher | Set-Content -Path $LauncherPath -Encoding ASCII
Write-Host "Created launcher: $LauncherPath" -ForegroundColor Green

# Create PowerShell launcher (better UX)
$PSLauncher = @"
# Tux Browser Launcher for Windows (PowerShell)

\$InstallDir = Split-Path -Parent \$MyInvocation.MyCommand.Definition
\$LibDir = Join-Path \$InstallDir '..\lib'
\$TorDir = Join-Path \$InstallDir '..\tor'
\$TorDataDir = Join-Path \$env:LOCALAPPDATA 'Tux Browser\tor'
\$ProfileDir = Join-Path \$env:LOCALAPPDATA 'Tux Browser\profile'

New-Item -ItemType Directory -Force -Path \$TorDataDir, \$ProfileDir | Out-Null

# Check if Tor is running
\$torRunning = Get-NetTCPConnection -LocalPort 9050 -State Listen -ErrorAction SilentlyContinue
if (-not \$torRunning) {
    # Try to start embedded Tor
    \$torExe = Join-Path \$TorDir 'tor.exe'
    if (Test-Path \$torExe) {
        \$torProcess = Start-Process -FilePath \$torExe -ArgumentList '--DataDirectory', \$TorDataDir, '--SOCKSPort', '9050', '--ControlPort', '9051', '--CookieAuthentication', '1', '--Log', 'notice stdout', '--AvoidDiskWrites', '1' -WindowStyle Hidden -PassThru
        
        # Wait for Tor to start
        for (\$i = 0; \$i -lt 30; \$i++) {
            Start-Sleep -Seconds 1
            \$torRunning = Get-NetTCPConnection -LocalPort 9050 -State Listen -ErrorAction SilentlyContinue
            if (\$torRunning) { break }
        }
        if (-not \$torRunning) {
            Write-Warning 'Tor failed to start within 30 seconds'
        }
    } else {
        Write-Warning 'Embedded Tor not found. Please install Tor from https://torproject.org'
        Write-Warning 'and ensure it'"'"'s running on localhost:9050'
    }
}

# Launch browser
\$browserExe = Join-Path \$LibDir 'tux-browser.exe'
\$args = @('--enable-features=TorNetworking', '--proxy-server=socks5h://127.0.0.1:9050', '--user-data-dir=' + \$ProfileDir) + \$args
Start-Process -FilePath \$browserExe -ArgumentList \$args
"@

$PSLauncherPath = Join-Path $BinDir "tux-browser.ps1"
$PSLauncher | Set-Content -Path $PSLauncherPath -Encoding UTF8
Write-Host "Created PowerShell launcher: $PSLauncherPath" -ForegroundColor Green

# Create Start Menu shortcut
$WshShell = New-Object -ComObject WScript.Shell
$StartMenu = if ($User) { $WshShell.SpecialFolders("StartMenu") } else { $WshShell.SpecialFolders("AllUsersStartMenu") }
$ShortcutPath = Join-Path $StartMenu "Programs\Tux Browser.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PSLauncherPath
$Shortcut.Arguments = ""
$Shortcut.WorkingDirectory = $BinDir
$Shortcut.Description = "Tux Browser - Privacy-focused browser with integrated Tor"
$Shortcut.IconLocation = (Join-Path $LibDir "tux-browser.exe,0")
$Shortcut.Save()
Write-Host "Created Start Menu shortcut" -ForegroundColor Green

# Create Desktop shortcut
$Desktop = if ($User) { $WshShell.SpecialFolders("Desktop") } else { $WshShell.SpecialFolders("AllUsersDesktop") }
$DesktopShortcutPath = Join-Path $Desktop "Tux Browser.lnk"
$DesktopShortcut = $WshShell.CreateShortcut($DesktopShortcutPath)
$DesktopShortcut.TargetPath = $PSLauncherPath
$DesktopShortcut.WorkingDirectory = $BinDir
$DesktopShortcut.Description = "Tux Browser - Privacy-focused browser with integrated Tor"
$DesktopShortcut.IconLocation = (Join-Path $LibDir "tux-browser.exe,0")
$DesktopShortcut.Save()
Write-Host "Created Desktop shortcut" -ForegroundColor Green

# Add to PATH (user)
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$BinDir*") {
    $newPath = $userPath + ";" + $BinDir
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
    Write-Host "Added to user PATH" -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now run Tux Browser from:" -ForegroundColor Cyan
Write-Host "  - Start Menu: Tux Browser"
Write-Host "  - Desktop shortcut: Tux Browser"
Write-Host "  - Command prompt: tux-browser"
Write-Host "  - PowerShell: tux-browser"
Write-Host ""
Write-Host "On first launch, Tux Browser will connect to Tor network (10-30 seconds)." -ForegroundColor Yellow
Write-Host "Visit https://check.torproject.org to verify your connection." -ForegroundColor Yellow