; Obsidian Minimize to System Tray
; AutoHotkey v2 script
; Poner en Startup: %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

#Requires AutoHotkey v2.0
#SingleInstance Force

OBSIDIAN_PATH := LocalAppData "\Obsidian\Obsidian.exe"
TRAY_MENU := A_ScriptName

; --- Launch Obsidian minimizado al iniciar Windows ---
if !ProcessExist("Obsidian.exe") {
    Run OBSIDIAN_PATH,, "Min", &pid
    Sleep 2000
}

; --- Hotkey: Win+Shift+O para toggle Obsidian ---
#+o:: {
    global OBSIDIAN_PATH
    if WinExist("ahk_class ObsidianMainWindow") {
        WinMinimize
    } else if ProcessExist("Obsidian.exe") {
        WinActivate
    } else {
        Run OBSIDIAN_PATH,, "Min"
    }
}

; --- Detectar minimize y mover a tray ---
; Obsidian usa clase ObsidianMainWindow en Windows 11
OnMessage(0x0016, WM_ACTIVATE)

WM_ACTIVATE(wParam, lParam, msg, hwnd) {
    if (wParam = 0 && WinGetClass("ahk_id " hwnd) = "ObsidianMainWindow") {
        WinHide("ahk_id " hwnd)
        TrayTip "Obsidian", "Minimizado a la bandeja del sistema", 10
    }
}

; --- Menu contextual en tray ---
A_TrayMenu.Delete()
A_TrayMenu.Add("Mostrar Obsidian", (*) => WinShow("ahk_class ObsidianMainWindow"))
A_TrayMenu.Add("Cerrar Obsidian", (*) => ProcessClose("Obsidian.exe"))
A_TrayMenu.Add()
A_TrayMenu.Add("Salir", (*) => ExitApp())
