# Optoblock

Optoblock is a private, local-first Windows productivity app for tasks, projects, notes, journaling, shopping, recipes, finances, routines, focus sessions, and quick brain dumps. It is built with Python and PySide6 and stores your information on your own computer.

## Download for Windows

### [Download Optoblock-Windows.zip](https://github.com/jjbees99/Optoblock/releases/latest/download/Optoblock-Windows.zip)

You do **not** need Python to use the downloadable app.

1. Download `Optoblock-Windows.zip` using the link above.
2. Right-click the downloaded ZIP and select **Extract All**.
3. Open the extracted `Optoblock` folder.
4. Double-click **`Optoblock.exe`**.

Keep the `_internal` folder beside `Optoblock.exe`; the application needs both. Windows may show a SmartScreen warning because the app is not code-signed. If you trust this repository, select **More info**, then **Run anyway**.

If the direct download link is unavailable, open the [latest release page](https://github.com/jjbees99/Optoblock/releases/latest) and download `Optoblock-Windows.zip` from **Assets**.

## Highlights

- Customisable 4 × 3 dashboard with draggable and resizable modules
- Smooth page fade-and-slide transitions
- Tasks with priorities, due dates, filters, completion, archive, and restore
- Projects with ideas, next actions, progress states, and task conversion
- Autosaving notes and daily journal entries with voice, writing, and drawing tools
- Grocery and general/Amazon shopping lists
- Recipes with one-click ingredient transfer to the grocery list
- Focus timer, voice brain dump, and unwind routines
- Spreadsheet-style finance tracking
- Bills, documents, errands, follow-ups, travel, and home administration pages
- Festival-inspired Cream, Ink, Peach, and Lilac colour schemes
- English and German workspace navigation, startup-module selection, and archive view
- Custom Optoblock cube branding across the sidebar and Windows application icon
- Local SQLite storage plus readable JSON snapshots and backup/restore

## Your data

Optoblock stores its working data in `%USERPROFILE%\.optoblock` rather than inside the application folder. The main database is `optoblock.sqlite3`; a readable copy is maintained at `data\optoblock-data.json`, and notes are also written to `data\notes` as UTF-8 text files.

Use Optoblock's JSON export before replacing a computer or making major changes. Installing a newer release does not intentionally remove your existing data.

## Run from source

Requirements:

- Windows 10 or 11
- Python 3.11 or newer
- A microphone for voice features
- Internet access for online speech recognition

Clone the repository, then run:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

Alternatively, the included installer performs the environment setup:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

## Build the Windows app

With the virtual environment active:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_windows.ps1
```

The executable is created at `dist\Optoblock\Optoblock.exe`. Distribute the entire `Optoblock` folder or a ZIP containing it—not the EXE by itself.

Tagged versions are built automatically by the GitHub Actions release workflow. The resulting `Optoblock-Windows.zip` is attached to the matching GitHub Release.

## Project layout

```text
Optoblock/
├── main.py                 Application entry point
├── personal_app/
│   ├── assets/             Icons and packaged assets
│   ├── data/               SQLite schema and data models
│   ├── gui/                PySide6 windows, pages, and styling
│   └── logic/              Feature and storage managers
├── tests/                  Automated tests
├── requirements.txt        Runtime dependencies
├── install.ps1             Source setup helper
├── build_windows.ps1       Windows packaging helper
└── Optoblock.spec          PyInstaller configuration
```

## Troubleshooting

- If `python` is not recognised, reinstall Python and select **Add Python to PATH**.
- If microphone input fails, allow desktop microphone access under Windows **Settings → Privacy & security → Microphone**.
- Voice transcription uses Google's recognition service and requires an internet connection.
- If SmartScreen appears, use **More info → Run anyway** only if you trust the downloaded release.
- Keep a copy of `%USERPROFILE%\.optoblock` before restoring or replacing data.

## Tests

```powershell
python -m unittest discover -s tests -v
```
