@echo off
echo Installing Claude Widget dependencies...
pip install pystray Pillow
echo.
echo Registering auto-start on login...
powershell -NoProfile -Command "$s = New-Object -ComObject WScript.Shell; $lnk = $s.CreateShortcut(\"$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\ClaudeWidget.lnk\"); $lnk.TargetPath = 'C:\ClaudeZone\claude-widget\launch.vbs'; $lnk.WorkingDirectory = 'C:\ClaudeZone\claude-widget'; $lnk.Save()"
echo.
echo Done! Widget will auto-start hidden in tray on every login.
echo Run launch.vbs now to test it.
pause
