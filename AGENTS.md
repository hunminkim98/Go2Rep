# Repository Guidelines

## Project Structure & Module Organization
Go2Rep centers on two entry points: `main_gui.py` for the Tkinter controller and `PerforMetrics/` for the Avalonia client plus FastAPI backend (`Backend/`). Shared Python tooling lives in `tools/` for capture, sync, and reports. `GoPro/` hosts vendor tutorials and BLE/COHN protobufs. Calibration assets stay in `calib/`, visual media in `Assets/`, and `Drafts/` remains for prototypes only.

## Build, Test, and Development Commands
- Backend setup: `cd PerforMetrics/Backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`.
- Legacy GUI: `conda activate Go2Rep` then `python main_gui.py` from the repo root.
- Full desktop stack: `cd PerforMetrics && python3 start_fullstack.py` (starts FastAPI and Avalonia together).
- Isolated services: `./Backend/start_backend.sh` (or `python main.py`) for the API; `dotnet build && dotnet run` for the Avalonia client.

## Coding Style & Naming Conventions
Follow PEP 8 in Python: four-space indents, snake_case modules such as `tools/gopro_capture.py`, typed async flows, and module-level hardware constants. FastAPI routes should expose docstrings and return explicit JSON. Avalonia code follows MVVM expectations—PascalCase classes/properties, camelCase private fields, `ReactiveCommand` for actions, and clean `DataContext` bindings in XAML.

## Testing Guidelines
Automated tests are absent, so lean on scenario checks. For Python tools, exercise BLE/WiFi hardware paths and watch logger output. Backend changes should run `uvicorn main:app --reload` (or `python main.py`) and hit `/health` plus `/api/system/info`. For UI work, run `dotnet run`, confirm the backend status indicator, and capture screenshots of updates. Log each manual test sequence in your PR.

## Commit & Pull Request Guidelines
History favors concise summaries (`for mac without GUI`); keep using present-tense lines like `Add COHN download retry` and group related edits together. PRs should state scope, list commands you ran, link issues, and share UI evidence when layouts change. Note configuration or credential impacts, especially under `certifications/` and calibration paths.

## Security & Configuration Tips
Never commit live GoPro certificates; rely on the placeholders in `certifications/`. Store site calibration `.toml` files outside Git and surface paths through `config.py`. Redact camera identifiers in shared logs and keep generated media in external workspaces referenced by `settings.GOPRO_WORKSPACE_PATH`.
