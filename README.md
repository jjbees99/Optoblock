# Optoblock

Optoblock is a local-first Windows app for organising tasks, projects, notes, shopping, your day and more. Your data stays on your computer.

## Download and start (Windows)

1. **[Download Optoblock for Windows](https://github.com/jjbees99/Optoblock/releases/latest/download/Optoblock-Windows.zip)**. If the download does not start, open the [latest release](https://github.com/jjbees99/Optoblock/releases/latest) and select **Optoblock-Windows.zip** under **Assets** (not “Source code”).
2. Open your Downloads folder, right-click the ZIP file and choose **Extract All**, then **Extract**.
3. Open the extracted **Optoblock** folder and double-click **Optoblock.exe**.
4. Keep the **_internal** folder alongside the EXE. You can move the whole extracted Optoblock folder wherever you like, and create a shortcut to the EXE.

No Python installation or command line is needed. The app is for Windows 10 and 11. Windows SmartScreen may warn that the app is unsigned; if you trust this download, choose **More info**, then **Run anyway**.

To update, download and extract the latest release the same way, then use the new folder. Your existing data is stored separately and should remain available.

## Your data

Optoblock stores its database and settings in `%USERPROFILE%\.optoblock`. To find it, paste that path into File Explorer's address bar. Back up this folder regularly and copy it to the same location on a new computer. The app also offers a JSON export and restore option.

## Phone access (optional)

You can access selected features from your phone while Optoblock is running on your PC. See [Phone access setup](PHONE_ACCESS_SETUP.md) for the steps. Phone access is optional and does not require opening a public firewall port.

## Run from source (developers)

Install [Python](https://www.python.org/downloads/windows/) 3.11 or newer and select **Add Python to PATH** during installation. Download the repository with **Code → Download ZIP** and extract it, or clone it with Git. Open PowerShell in the extracted project folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
.\.venv\Scripts\python.exe main.py
```

A microphone and internet connection are needed for online voice transcription. The app's other features do not require voice input.

To run tests:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

To build the Windows app from source, activate the virtual environment and run `powershell -NoProfile -ExecutionPolicy Bypass -File .\build_windows.ps1`. The complete app is created in `dist\Optoblock`; distribute the whole folder, not just the EXE. Tagged versions are built and published by GitHub Actions.

## Troubleshooting

- **The app does not open from the ZIP:** extract all files first, and keep `_internal` next to `Optoblock.exe`.
- **SmartScreen appears:** the app is unsigned. If you trust the release, select **More info → Run anyway**.
- **Microphone input fails:** allow desktop microphone access in Windows **Settings → Privacy & security → Microphone**. Online transcription needs an internet connection.
- **Python is not recognised:** reinstall Python and enable **Add Python to PATH**. Python is only needed when running from source.
