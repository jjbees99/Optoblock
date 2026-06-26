$ErrorActionPreference = "Stop"
python -m pip install -r requirements.txt
python -m pip install pyinstaller
pyinstaller --noconfirm --windowed --name Momentum --icon personal_app/assets/darg_app_icon.ico main.py
