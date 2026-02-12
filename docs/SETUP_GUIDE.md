# Setup Guide

Complete setup instructions for the Wall Ball AR Arcade system.

---

## Prerequisites

### Hardware Requirements

**Minimum:**
- CPU: Intel i5 / AMD Ryzen 5 (4+ cores)
- RAM: 8GB
- GPU: NVIDIA GTX 1050 (2GB VRAM) with CUDA support
- Camera: USB webcam or IP camera (720p @ 30fps)
- Projector: 1080p capable
- Wall: Flat surface (white recommended)

**Recommended:**
- CPU: Intel i7 / AMD Ryzen 7 (6+ cores)
- RAM: 16GB
- GPU: NVIDIA RTX 2060 (6GB VRAM)
- Camera: High-speed camera (1080p @ 60fps)
- Projector: 1080p @ 60Hz
- Network: Gigabit Ethernet or 5GHz WiFi

### Software Requirements

**Operating System:**
- Windows 10/11 (primary support)
- Linux Ubuntu 20.04+ (secondary support)
- macOS (limited support, no CUDA)

**Python:**
- Python 3.8 - 3.10
- pip package manager
- virtualenv (recommended)

**Unity:**
- Unity 2020.3 LTS or newer
- Unity Hub (recommended)

**CUDA (for GPU acceleration):**
- NVIDIA CUDA Toolkit 12.1+
- cuDNN 8.9+

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/gkalyan78725-eng/WallBallArcade.git
cd WallBallArcade
```

### 2. Python Vision Engine Setup

#### Create Virtual Environment

```bash
cd vision_engine
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

**Package Installation Order (if issues):**
1. Install PyTorch with CUDA first:
   ```bash
   pip install torch==2.6.0 torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu121
   ```

2. Install other dependencies:
   ```bash
   pip install opencv-python opencv-contrib-python numpy ultralytics pyyaml filterpy websockets loguru
   ```

#### Verify CUDA Installation

```python
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

Expected output: `CUDA available: True`

If False, check:
- NVIDIA drivers installed
- CUDA Toolkit installed
- PyTorch CUDA version matches CUDA Toolkit

#### Download YOLO Model

The YOLOv8 nano model will download automatically on first run:

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

Model location: `~/.cache/torch/hub/ultralytics/yolov8/`

### 3. Unity Client Setup

#### Install Unity

1. Download Unity Hub from https://unity.com/download
2. Install Unity 2020.3 LTS or newer
3. Add necessary modules:
   - Windows Build Support
   - Linux Build Support (optional)

#### Open Project

1. Open Unity Hub
2. Click "Add" → "Add project from disk"
3. Navigate to `WallBallArcade/unity_client`
4. Open project in Unity

#### Install TextMeshPro (if prompted)

Unity will prompt to import TextMeshPro essentials on first open:
- Click "Import TMP Essentials"
- Wait for import to complete

---

## Configuration

### Vision Engine Configuration

Edit `vision_engine/config/settings.yaml`:

#### Camera Settings

```yaml
camera:
  index: 0              # Camera device index (0 = default)
  width: 1280          # Frame width
  height: 720          # Frame height
  fps: 60              # Target FPS
  buffer_size: 1       # Low latency buffer
  backend: "DSHOW"     # Windows: DSHOW, Linux: V4L2
```

**Find Camera Index (Windows):**
```bash
python -c "import cv2; [print(f'Camera {i}') for i in range(10) if cv2.VideoCapture(i).isOpened()]"
```

#### Detection Settings

```yaml
detection:
  model: "yolov8n.pt"           # Model size: n/s/m/l/x
  confidence_threshold: 0.45     # Detection confidence
  iou_threshold: 0.4            # NMS threshold
  imgsz: 640                    # Input size
  device: "cuda"                # cuda or cpu
  half_precision: true          # FP16 acceleration
  max_det: 5                    # Max detections
```

**Model Selection:**
- `yolov8n.pt` - Fastest, 3ms (recommended)
- `yolov8s.pt` - Balanced, 5ms
- `yolov8m.pt` - Accurate, 10ms
- `yolov8l.pt` - Very accurate, 20ms

#### Network Settings

```yaml
network:
  protocol: "udp"               # udp or websocket
  udp_host: "127.0.0.1"        # Unity client IP
  udp_port: 9000               # Unity listening port
  websocket_uri: "ws://localhost:9001"
```

**For Remote Unity Client:**
```yaml
udp_host: "192.168.1.100"  # Replace with Unity machine IP
```

### Unity Client Configuration

Configure in Unity Inspector:

#### HitReceiver Component

1. Select GameObject with HitReceiver
2. Set protocol: UDP or WebSocket
3. Set UDP Port: 9000
4. Configure coordinate transform:
   - Enable "Normalize Coordinates"
   - Set World Size: (10, 10)
   - Set World Offset: (-5, -5)

#### Game Modes

Each game mode has configurable parameters in Inspector:
- Brick count, spacing, points
- Target spawn rate, size, scoring
- Reaction timing, difficulty

---

## First Run

### 1. Camera Test

Test camera capture:

```bash
cd vision_engine
python -c "import cv2; cap = cv2.VideoCapture(0); ret, frame = cap.read(); print(f'Camera OK: {ret}, Shape: {frame.shape if ret else None}')"
```

### 2. Calibration

**Setup:**
1. Position camera to view entire projection wall
2. Ensure good lighting (avoid shadows)
3. Start projector and display on wall

**Run Calibration:**

```bash
python main.py calibrate --camera 0 --wall-width 1920 --wall-height 1080
```

**Process:**
1. Camera view window appears
2. Click 4 wall corners in order:
   - Top-left corner of projected area
   - Top-right corner
   - Bottom-right corner
   - Bottom-left corner
3. Calibration computes automatically
4. Press 'q' to accept, 'r' to reset

**Validation:**

```bash
python main.py calibrate --camera 0 --test
```

Click anywhere on camera view to see transformed coordinates.

**Calibration File:**
- Saved to: `vision_engine/config/calibration.json`
- Backup this file after successful calibration

### 3. Vision Engine Test

Run with debug visualization:

```bash
python main.py test
```

**Expected:**
- Window showing camera feed
- FPS counter in top-left
- Bounding boxes around detected balls
- Trajectory lines
- Hit markers on wall hits

**Troubleshooting:**
- No detections? Adjust `confidence_threshold` lower
- Low FPS? Check GPU usage, reduce resolution
- Jumpy tracking? Adjust Kalman noise parameters

### 4. Unity Test

**Setup Scene:**
1. Open Unity project
2. Create empty scene
3. Add GameObjects:
   - GameManager (with GameManager.cs)
   - HitReceiver (with HitReceiver.cs)
   - ScoreManager (with ScoreManager.cs)
   - DebugOverlay (with DebugOverlay.cs)

**Run Unity:**
1. Press Play in Unity Editor
2. Open Debug Overlay (F1 key)
3. Check "Network Connected: True"

**Test Hit Reception:**
1. Start vision engine: `python main.py run`
2. Throw ball at wall
3. Verify in Unity:
   - Debug overlay shows message count increasing
   - "Last Hit: X.Xs ago" updates
   - Console shows hit coordinates

---

## Network Setup

### Local Machine (Easiest)

Vision engine and Unity on same computer:
- Use default settings
- No firewall configuration needed
- Lowest latency

### Separate Machines (Recommended)

**Vision Engine Machine:**
- Configure `udp_host` to Unity machine IP
- Ensure firewall allows UDP port 9000 outbound

**Unity Machine:**
- Ensure firewall allows UDP port 9000 inbound
- Configure HitReceiver with same port

**Test Connection:**

Vision machine:
```bash
ping <unity-machine-ip>
```

Unity machine:
```bash
# Windows
Test-NetConnection -ComputerName <vision-machine-ip> -Port 9000

# Linux
nc -zv <vision-machine-ip> 9000
```

### Firewall Configuration

**Windows:**
```powershell
New-NetFirewallRule -DisplayName "WallBall UDP" -Direction Inbound -Protocol UDP -LocalPort 9000 -Action Allow
```

**Linux:**
```bash
sudo ufw allow 9000/udp
```

---

## Verification Checklist

- [ ] Python dependencies installed
- [ ] CUDA available and working
- [ ] YOLO model downloaded
- [ ] Camera accessible
- [ ] Calibration completed
- [ ] Unity project opens without errors
- [ ] Network connection working
- [ ] Hit events received in Unity
- [ ] Game modes functional
- [ ] Performance meets targets (60+ FPS)

---

## Common Issues

### Camera Not Found

**Error:** `Failed to open camera`

**Solutions:**
1. Check camera is connected and powered
2. Try different camera index (0, 1, 2...)
3. Check camera not used by another application
4. Update camera drivers
5. Try different backend (DSHOW, V4L2, MSMF)

### CUDA Not Available

**Error:** `CUDA not available, falling back to CPU`

**Solutions:**
1. Install NVIDIA drivers
2. Install CUDA Toolkit
3. Reinstall PyTorch with CUDA:
   ```bash
   pip uninstall torch torchvision
   pip install torch==2.6.0 torchvision==0.19.0 --index-url https://download.pytorch.org/whl/cu121
   ```
4. Verify with: `nvidia-smi`

### Low FPS

**Symptoms:** FPS below 30, laggy detection

**Solutions:**
1. Enable GPU acceleration (CUDA)
2. Reduce camera resolution (640x480)
3. Use smaller YOLO model (yolov8n.pt)
4. Close other GPU applications
5. Reduce `imgsz` to 320 or 416

### No Hit Detection

**Symptoms:** Ball detected but no hits registered

**Solutions:**
1. Check calibration is loaded
2. Adjust `velocity_threshold` (try -30)
3. Lower `hit_confirmation_frames` (try 1)
4. Increase `direction_change_angle` (try 90)
5. Verify ball moving fast enough

### Unity Not Receiving Messages

**Symptoms:** "Connected: False" in debug overlay

**Solutions:**
1. Check vision engine is running
2. Verify IP addresses match
3. Check firewall settings
4. Confirm port numbers match (9000)
5. Try localhost first (127.0.0.1)
6. Check for port conflicts

---

## Next Steps

After successful setup:
1. Read [CALIBRATION.md](CALIBRATION.md) for advanced calibration
2. Read [PERFORMANCE_TUNING.md](PERFORMANCE_TUNING.md) for optimization
3. Review [API_REFERENCE.md](API_REFERENCE.md) for customization
4. Check [ARCHITECTURE.md](ARCHITECTURE.md) for system understanding
