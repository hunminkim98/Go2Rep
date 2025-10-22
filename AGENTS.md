# Repository Guidelines

## Project Structure & Module Organization
- `main_gui.py`: legacy Tkinter launcher that still drives camera, sync, and reporting flows.
- `tools/`: shared Python modules for BLE/WiFi control, calibration, Theia prep, and reports; imported wherever functionality is exposed.
- `GoPro/`: protocol adapters and tutorial code—treat this as the SDK layer and coordinate signature changes with consumers.
- `PerforMetrics/`: Avalonia desktop client plus FastAPI backend (`Backend/`); launcher scripts live beside the C# project, while reference data sits in `calib/`, `Assets/`, and `certifications/`.

## Build, Test, and Development Commands
- `python3 start_fullstack.py`: validates the Go2Rep conda env, installs backend deps, launches FastAPI and Avalonia together.
- `cd PerforMetrics/Backend && source venv/bin/activate && uvicorn main:app --reload`: backend only; use `start_backend.sh|.bat` for scripted startup.
- `dotnet build PerforMetrics/PerforMetrics.csproj` then `dotnet run`: compile or debug the Avalonia UI independently.
- `python main_gui.py`: bring up the legacy interface when reproducing existing workflows or triaging regressions.

## Coding Style & Naming Conventions
- Python: follow PEP 8 with 4-space indentation, descriptive snake_case names, and guard script entry with `if __name__ == "__main__"`.
- Centralise reusable logic in `tools/` and document async behaviour or hardware assumptions in module docstrings.
- C#: stick to .NET casing; keep XAML names aligned with matching view models to preserve MVVM bindings.

## Testing Guidelines
- Place FastAPI tests under `PerforMetrics/Backend/tests/` using `pytest` with `httpx.AsyncClient`; run `python -m pytest PerforMetrics/Backend/tests` inside the venv.
- Plan future Avalonia tests in a `PerforMetrics.Tests` project and execute with `dotnet test`; attach screenshots or screencasts for interim UI validation.
- Record manual QA steps for camera connectivity or hardware-dependent paths in the PR description.

## Commit & Pull Request Guidelines
- Write imperative commit subjects ≤72 chars (e.g., `feat: add BLE scan retries`) and add short bodies for behavioural changes.
- Reference issues (`Refs #123`) and avoid bundling unrelated refactors; squash fixups before requesting review.
- PRs must list executed checks, call out config or asset updates, and include visuals for UI-affecting work.

## Security & Configuration Tips
- Keep certificates and WiFi secrets out of Git; store them locally under `certifications/` and load via environment variables or ignored config files.
- Verify `appsettings.json`, backend `.env` files, and launcher scripts do not ship real credentials.
- Share large calibration/media assets through links and document the expected install paths instead of committing binaries.
