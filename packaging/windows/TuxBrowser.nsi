; Tux Browser - NSIS Installer Script
; Creates a professional Windows installer (.exe)
; Requires: NSIS v3.08+ (nsis.sourceforge.io)

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"

;===============================================================================
; Configuration
;===============================================================================
!define PRODUCT_NAME "Tux Browser"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "Tux Browser Team"
!define PRODUCT_WEB_SITE "https://tuxbrowser.org"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\Tux Browser"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; Build-time variables (override with /D on command line)
!define BINARY_SOURCE "..\..\chromium-main\chromium-main\out\tux_browser"
!define TOR_SOURCE "..\..\tor-expert-bundle-windows-x64\tor"
!define OUTPUT_DIR "..\output"

;===============================================================================
; MUI Settings
;===============================================================================
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

!define MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\modern-wizard.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\modern-wizard.bmp"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

;===============================================================================
; General Settings
;===============================================================================
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "${OUTPUT_DIR}\TuxBrowser-${PRODUCT_VERSION}-Setup-x64.exe"
InstallDir "$PROGRAMFILES64\Tux Browser"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
RequestExecutionLevel admin
CRCCheck on
WindowIcon on
ShowInstDetails show
ShowUninstDetails show

;===============================================================================
; Variables
;===============================================================================
Var TorRunning
Var PreviousVersion

;===============================================================================
; Sections
;===============================================================================
Section "Main Application" SEC_MAIN
  SectionIn RO
  
  ; Create directories
  CreateDirectory "$INSTDIR\bin"
  CreateDirectory "$INSTDIR\lib"
  CreateDirectory "$INSTDIR\tor\pluggable_transports"
  
  ; Browser binary
  File "/oname=tux-browser.exe" "${BINARY_SOURCE}\chrome.exe"
  
  ; Launcher scripts
  File "..\..\install_windows.bat"
  File "..\..\install_windows.ps1"
  
  ; Set uninstall registry keys
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "QuietUninstallString" "$INSTDIR\Uninstall.exe /S"
  WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoRepair" 1
  
  ; App Paths for command line access
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\App Paths\Tux Browser" "" "$INSTDIR\bin\tux-browser.ps1"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\App Paths\Tux Browser" "Path" "$INSTDIR\bin"
  
SectionEnd

Section "Embedded Tor" SEC_TOR
  ; Tor executable and dependencies
  File "${TOR_SOURCE}\tor.exe"
  File "${TOR_SOURCE}\libcrypto-3-x64.dll"
  File "${TOR_SOURCE}\libssl-3-x64.dll"
  File "${TOR_SOURCE}\libevent-2.1-7.dll"
  
  ; Set section as selected by default
  SectionIn 1
SectionEnd

Section "Pluggable Transports" SEC_TRANSPORTS
  ; obfs4proxy
  File "${TOR_SOURCE}\pluggable_transports\obfs4proxy.exe"
  
  ; Snowflake client (if available)
  File "${TOR_SOURCE}\pluggable_transports\snowflake-client.exe"
  
  ; Conjure client (if available)
  File "${TOR_SOURCE}\pluggable_transports\conjure-client.exe"
  
  SectionIn 1
SectionEnd

Section "Shortcuts" SEC_SHORTCUTS
  ; Create Start Menu folder
  CreateDirectory "$SMPROGRAMS\Tux Browser"
  
  ; Start Menu shortcut
  CreateShortCut "$SMPROGRAMS\Tux Browser\Tux Browser.lnk" "$INSTDIR\bin\tux-browser.ps1" "" "$INSTDIR\lib\tux-browser.exe" 0
  
  ; Uninstall shortcut
  CreateShortCut "$SMPROGRAMS\Tux Browser\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
  
  ; Desktop shortcut (optional - ask user)
  ${If} $DESKTOP_SHORTCUT == "1"
    CreateShortCut "$DESKTOP\Tux Browser.lnk" "$INSTDIR\bin\tux-browser.ps1" "" "$INSTDIR\lib\tux-browser.exe" 0
  ${EndIf}
  
  SectionIn 1
SectionEnd

;===============================================================================
; Custom Pages
;===============================================================================
Var DESKTOP_SHORTCUT

!insertmacro MUI_PAGE_CUSTOM CreateDesktopPage ShowDesktopPage
Function CreateDesktopPage
  !insertmacro MUI_HEADER_TEXT "Choose Shortcuts" "Select additional shortcuts to create"
  nsDialogs::Create 1018
  Pop $0
  
  ${NSD_CreateCheckbox} 20 20 100% 15 "Create Desktop shortcut"
  Pop $DESKTOP_SHORTCUT
  ${NSD_Check} $DESKTOP_SHORTCUT
  
  nsDialogs::Show
FunctionEnd

Function ShowDesktopPage
  ${NSD_GetState} $DESKTOP_SHORTCUT $0
  ${If} $0 == ${BST_CHECKED}
    StrCpy $DESKTOP_SHORTCUT "1"
  ${Else}
    StrCpy $DESKTOP_SHORTCUT "0"
  ${EndIf}
FunctionEnd

;===============================================================================
; Functions
;===============================================================================
Function .onInit
  ; Check if running on 64-bit Windows
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "This installer only supports 64-bit Windows."
    Abort
  ${EndIf}
  
  ; Check for previous installation
  ReadRegStr $PreviousVersion HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion"
  ${If} $PreviousVersion != ""
    MessageBox MB_YESNO "A previous version (${PreviousVersion}) is installed. Upgrade?" IDYES +2
    Abort
  ${EndIf}
  
  ; Check if Tor is running
  ${CheckTorRunning} $TorRunning
FunctionEnd

Function CheckTorRunning
  Push $0
  Push $1
  System::Call 'iphlpapi.dll::GetExtendedTcpTable(i 0, i *i0r1, i 1, i 2, i 0, i 0) i.r0'
  StrCmp $0 0 +3
  StrCpy $1 1
  Goto +2
  StrCpy $1 0
  Pop $0
  Exch $1
FunctionEnd

;===============================================================================
; Installer Event Handlers
;===============================================================================
Function .onInstSuccess
  ; Create Tor data directories
  CreateDirectory "$LOCALAPPDATA\Tux Browser\tor"
  CreateDirectory "$LOCALAPPDATA\Tux Browser\profile"
  
  ; Add to PATH (user)
  ReadRegStr $0 HKCU "Environment" "PATH"
  StrStr $0 $0 "$INSTDIR\bin"
  ${If} $0 == ""
    ReadRegStr $0 HKCU "Environment" "PATH"
    StrCpy $1 "$0;$INSTDIR\bin"
    WriteRegStr HKCU "Environment" "PATH" $1
    ; Broadcast environment change
    SendMessage ${HWND_BROADCAST} ${WM_SETTINGCHANGE} 0 "STR:Environment" /TIMEOUT=5000
  ${EndIf}
FunctionEnd

;===============================================================================
; Uninstaller
;===============================================================================
Section Uninstall
  ; Remove files
  Delete "$INSTDIR\bin\tux-browser.exe"
  Delete "$INSTDIR\bin\tux-browser.bat"
  Delete "$INSTDIR\bin\tux-browser.ps1"
  Delete "$INSTDIR\lib\tux-browser.exe"
  Delete "$INSTDIR\tor\tor.exe"
  Delete "$INSTDIR\tor\libcrypto-3-x64.dll"
  Delete "$INSTDIR\tor\libssl-3-x64.dll"
  Delete "$INSTDIR\tor\libevent-2.1-7.dll"
  Delete "$INSTDIR\tor\pluggable_transports\obfs4proxy.exe"
  Delete "$INSTDIR\tor\pluggable_transports\snowflake-client.exe"
  Delete "$INSTDIR\tor\pluggable_transports\conjure-client.exe"
  
  ; Remove shortcuts
  Delete "$SMPROGRAMS\Tux Browser\Tux Browser.lnk"
  Delete "$SMPROGRAMS\Tux Browser\Uninstall.lnk"
  Delete "$DESKTOP\Tux Browser.lnk"
  RMDir "$SMPROGRAMS\Tux Browser"
  
  ; Remove directories
  RMDir "$INSTDIR\tor\pluggable_transports"
  RMDir "$INSTDIR\tor"
  RMDir "$INSTDIR\lib"
  RMDir "$INSTDIR\bin"
  RMDir "$INSTDIR"
  
  ; Remove registry keys
  DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\App Paths\Tux Browser"
  
  ; Remove from PATH (user)
  ReadRegStr $0 HKCU "Environment" "PATH"
  ${If} $0 != ""
    StrReplace $0 "$0" "$INSTDIR\bin;" ""
    WriteRegStr HKCU "Environment" "PATH" $0
    SendMessage ${HWND_BROADCAST} ${WM_SETTINGCHANGE} 0 "STR:Environment" /TIMEOUT=5000
  ${EndIf}
  
  ; Remove user data (optional)
  MessageBox MB_YESNO "Remove user data (Tor circuits, profile)?" IDYES +2
  RMDir /r "$LOCALAPPDATA\Tux Browser"
SectionEnd

Function un.onUninstSuccess
  ; Clean up
  HideWindow
FunctionEnd

;===============================================================================
; Build
;===============================================================================
; Usage: makensis /DVERSION=1.0.0 TuxBrowser.nsi