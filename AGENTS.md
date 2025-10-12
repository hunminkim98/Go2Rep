# Repository Guidelines

## Project Structure & Module Organization
- `main_gui.py` is the Tkinter entry point that wires all GoPro workflows through `Go2Rep.tools`.
- `tools/` contains production modules for BLE provisioning, capture, video download, Theia classification, calibration, reporting, and power management; each is imported by the GUI layer.
- `calib/` stores calibration configs (`*.toml`) and reference tracks that feed `tools.calib_scene`; keep folder structure intact when adding new cameras.
- `Assets/` holds UI imagery and GIFs; `certifications/` carries GoPro certificates and credentials—replace with environment-specific copies rather than editing in place.
- `Drafts/` captures experimental scripts and sample data. Treat it as reference; do not import it in shipping code.

## Build, Test, and Development Commands
- `conda activate Go2Rep` – align with the environment described in `README.md` (bleak, tkcalendar, nest_asyncio, tutorial_modules, FFmpeg).
- `python main_gui.py` – launch the controller; run from the repository root.
- `python -m compileall tools` – quick regression check for syntax errors before opening a pull request.
- `ffprobe path/to/video.mp4` – validate that local FFmpeg is available; required by `tools.timecode_synchronizer`.

## Coding Style & Naming Conventions
- Follow PEP 8: 4-space indentation, `snake_case` for functions, `CamelCase` for widgets/classes, and module-level constants in `UPPER_CASE`.
- Prefer explicit async helpers over inline callbacks; share reusable BLE logic inside `tools` and import via `Go2Rep.tools.*`.
- Use docstrings for long coroutines or GUI flows and keep Windows paths raw (e.g., `r"C:\\..."`) to match existing patterns.

## Testing Guidelines
- There is no automated test suite; rely on manual verification by launching `python main_gui.py` and stepping through key flows (scan, connect, capture, download, classify).
- Use sample assets in `Drafts/My_Codes_NoGUI` for dry runs, and confirm `tools.timecode_synchronizer` produces `Synchronisation/output.json` and `video_offsets.csv`.
- Document device-dependent bugs in the Wiki or README.

## PerforMetrics v2.0 Testing (Week 7-8)

### MVVM Integration Smoke Test
**Prerequisites:** Mock mode enabled (`Container(use_mock=True)`)

**Test Steps:**
1. **App Launch**
   - [ ] `python go2rep/main.py` 실행
   - [ ] 앱이 정상적으로 시작되고 메인 윈도우 표시
   - [ ] 사이드바와 탑바가 정상 표시
   - [ ] 스크롤 기능 정상 동작

2. **Camera Section Navigation**
   - [ ] 사이드바에서 "Cameras" 클릭
   - [ ] Camera Management 섹션이 표시됨
   - [ ] 스크롤로 모든 UI 요소 접근 가능

3. **Scan Workflow**
   - [ ] "Scan for Cameras" 버튼 클릭
   - [ ] 로딩 스피너 표시 및 버튼 비활성화
   - [ ] 약 1초 후 Mock 카메라 3개 목록 표시
   - [ ] 버튼 다시 활성화

4. **Connect Workflow**
   - [ ] 카메라 목록에서 첫 번째 항목 선택
   - [ ] "Connect" 버튼 클릭
   - [ ] 연결 중 상태 표시 (약 2초)
   - [ ] 연결 성공 시 상태가 "Connected"로 변경
   - [ ] 상태 라벨에 "Connected to gopro_001" 표시

5. **Disconnect Workflow**
   - [ ] 연결된 카메라 선택
   - [ ] "Disconnect" 버튼 클릭
   - [ ] 연결 해제 중 상태 표시 (약 0.5초)
   - [ ] 연결 해제 성공 시 상태가 "Disconnected"로 변경
   - [ ] 상태 라벨에 "Disconnected from gopro_001" 표시

6. **Error Handling**
   - [ ] 동시에 여러 작업 시도 (연결 중 스캔 등)
   - [ ] 버튼들이 적절히 비활성화됨
   - [ ] Mock 어댑터의 10% 실패율로 인한 에러 처리 확인

**Expected Results:**
- 모든 비동기 작업이 UI를 블록하지 않음
- 상태 변경이 실시간으로 UI에 반영됨
- 에러 메시지가 적절히 표시됨
- 스크롤이 모든 섹션에서 정상 동작

**Known Limitations:**
- Mock 모드에서는 실제 하드웨어 연결 불가
- 네트워크 타임아웃이나 인증 에러 시뮬레이션 없음
- 배터리 레벨과 신호 강도는 랜덤 값으로 고정

## Commit & Pull Request Guidelines
- Recent commits favor short, Title Case summaries such as "Update README.md"; match that tone but add module context (e.g., "Tools: Harden BLE retry loop").
- Keep diffs focused: separate GUI tweaks from backend tooling changes.
- Pull requests should state the scenario tested, list any new media/config paths, and include screenshots for GUI updates.
- Link to supporting datasets or credentials handling steps rather than uploading sensitive files.

## Security & Configuration Tips
- Never commit live GoPro credentials; drop placeholders in `certifications/` and share actual files out-of-band.
- Ensure `tutorial_modules` and FFmpeg binaries are installed locally; they are required dependencies but not vendored.
