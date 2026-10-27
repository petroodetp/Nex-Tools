@echo off
echo Installation des dependances...
pip install -r requirements.txt || goto :err

echo Compilation de Nex Tools...
python -m PyInstaller --noconfirm --clean --onefile --windowed --uac-admin ^
  --name "NexTools" ^
  --icon "logo.ico" ^
  --add-data "logo.png;." ^
  --add-data "logo.ico;." ^
  --collect-all customtkinter ^
  main.py || goto :err

echo.
echo Termine : dist\NexTools.exe
pause
exit /b 0

:err
echo Erreur pendant la compilation.
pause
exit /b 1
