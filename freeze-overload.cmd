REM Overload Pyinstaller command to package app as Windows executable file
pyinstaller --clean --windowed --onefile ^
    --additional-hooks-dir=. ^
    --icon=".\icons\SledgeHammer.ico" ^
    --add-data="./icons;icons" ^
    --add-data="./rules;rules" ^
    --add-data="./help;help" ^
    --add-data="version.txt;." ^
    --version-file="windows_version_info.txt" ^
    overload.py
