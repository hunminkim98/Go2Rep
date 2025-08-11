# Go2Rep
Go2Rep is a GUI for multi-GoPro HERO (tested on GoPro 11/13) video collection and processing (COHN or BLE+AP). It supports camera control, video sync, Theia classification, calibration, and report generation—built for markerless 3D motion capture using wireless GoPro workflows.

<img src="Assets/Image1.png" alt="Go2Rep GUI" width="1000">



Go2Rep provides a unified interface for controlling multiple GoPro HERO cameras (tested on HERO11 and HERO13) over wireless connections.  
It handles the full workflow from discovery and connection to recording, downloading, and organizing videos.  
The application automatically adapts its communication method based on the camera model, ensuring the correct protocol is used for reliable control and media transfer.

Key capabilities include:
- **Camera discovery** via Bluetooth or COHN
- **Connection management** for one or more GoPros
- **Recording controls** (start/stop, FPS, resolution)
- **Automatic media collection** with proper handling of encrypted downloads
- **Model-specific workflows** to match protocol and provisioning requirements

---
            
                        | Feature                | GoPro 11 or older | GoPro 13 / 12   |
                        |------------------------|-------------------|-----------------|
                        | **Protocols Used**     | BLE + WiFi AP     | HTTPS via COHN  |
                        | **Certificate Provisioning** | ❌ Not Required  | ✅ Required     |
                        | **Preview & Streaming**| Supported via WiFi AP | Supported via COHN* |
                        | **Media Download**     | Basic via BLE + WiFi | Encrypted via HTTPS |
