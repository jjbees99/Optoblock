# Momentum

Momentum is a personal desktop productivity app for tasks, projects, shopping, recipes, unwind routines, and quick daily focus.

The app is built with Python and PySide6. It saves data locally in SQLite and supports JSON export/import for backups.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

## Package Later

PyInstaller support is scaffolded through `build_windows.ps1`.

```powershell
.\build_windows.ps1
```

The packaged app will be created in `dist/`.

## Features

- Modular table layout with selectable compartments
- Dashboard with daily focus and live summaries
- Tasks with edit, complete, archive, restore, delete, priorities, due dates, and filters
- Project ideas with next actions and task conversion
- Grocery and Amazon/general shopping lists
- Recipe ingredients that can be added to grocery shopping
- Unwind routines with random suggestions and daily reset
- Brain dump and quick add
- Archive view
- Settings with theme and startup module choices
- JSON export/import
