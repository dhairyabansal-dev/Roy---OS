$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $root "launcher\AgentBayLauncher.bat"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Agent Bay.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $launcher
$shortcut.WorkingDirectory = $root
$shortcut.Description = "Personal AI Mission Control"
$icon = Get-ChildItem -Path $root -Include *.ico,*.exe -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
$shortcut.IconLocation = if ($icon) { "$($icon.FullName),0" } else { "$env:SystemRoot\System32\SHELL32.dll,13" }
$shortcut.Save()
Write-Host "Created $shortcutPath"