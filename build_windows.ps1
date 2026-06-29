$ErrorActionPreference = "Stop"
python -m pip install -r requirements.txt
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --windowed --name Optoblock --icon personal_app/assets/darg_app_icon.ico main.py
