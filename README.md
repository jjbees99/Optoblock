# Optoblock

Optoblock is a Windows desktop productivity app for organising tasks, projects, shopping, recipes, routines, finances, focus sessions, and quick brain dumps. It is built with Python and PySide6, stores your information locally in SQLite, and supports JSON backup and restore.

## Download the ready-to-run Windows app

The easiest option does not require Python or any library installation:

1. Open the [latest GitHub release](https://github.com/jjbees99/Optoblock/releases/latest).
2. Download `Optoblock-Windows.zip` from **Assets**.
3. Extract the entire ZIP file to a folder on your computer.
4. Open the extracted `Optoblock` folder and double-click `Optoblock.exe`.

Keep the `_internal` folder beside `Optoblock.exe`; the application needs it to run. Windows may show a SmartScreen warning because the app is not code-signed. If you trust this repository, choose **More info**, then **Run anyway**.

## Run from source

### Requirements

- Windows 10 or 11
- Python 3.11 or newer (64-bit recommended)
- `pip`, included with a standard Python installation
- A microphone if you want to use voice brain dump
- An internet connection for online speech recognition

When installing Python from [python.org](https://www.python.org/downloads/windows/), select **Add Python to PATH**.

### Libraries

The required Python libraries are listed in `requirements.txt` and installed together:

- `PySide6` — desktop interface and Qt widgets
- `sounddevice` — microphone audio capture
- `SpeechRecognition` — converting recorded speech into text

PyInstaller is only required if you want to create the packaged Windows app; it is installed automatically by the build script.

### Installation

Open PowerShell in the project folder and run:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

This creates an isolated environment so Optoblock's libraries do not interfere with other Python projects.

### Start Optoblock

With the virtual environment activated, run:

```powershell
python main.py
```

On first use of voice input, allow microphone access if Windows asks. You can also enable it under **Settings > Privacy & security > Microphone**.

## Build the Windows package

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\Activate.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_windows.ps1
```

The script installs the runtime libraries and PyInstaller, then creates the complete app in `dist\Optoblock`. Distribute that whole folder, or compress it into a ZIP; do not distribute the EXE by itself.

## Features

- Customisable dashboard with movable and resizable compartments
- Tasks with priorities, due dates, filters, completion, archive, and restore
- Project ideas, next actions, and task conversion
- Grocery and general/Amazon shopping lists
- Recipe ingredients that can be sent to the grocery list
- Focus timer and voice brain dump
- Unwind routines with suggestions and daily reset
- Spreadsheet-style finance tracking
- Settings, themes, startup module selection, and archive view
- Local SQLite storage and JSON backup/restore

## Data and backups

Optoblock keeps its working data locally on your computer. Use the app's JSON export/import feature to make portable backups, especially before replacing or moving an installation.

## Tests

The tests use Python's built-in `unittest`, so no extra testing library is needed:

```powershell
python -m unittest discover -s tests -v
```
