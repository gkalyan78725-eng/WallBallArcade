# Performance Tuning Guide

Optimize the Wall Ball AR Arcade system for maximum performance and minimal latency.

---

## Performance Targets

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Vision Engine FPS | 60+ | 45-60 | <45 |
| Detection Latency | <15ms | 15-25ms | >25ms |
| Network Latency | <5ms | 5-10ms | >10ms |
| End-to-End Latency | <40ms | 40-60ms | >60ms |
| Frame Drop Rate | <1% | 1-5% | >5% |

---

## GPU Optimization

### CUDA Configuration

**Enable FP16 Half-Precision:**

Benefits: 2x speedup, 50% memory reduction

```yaml
detection:
  half_precision: true
  device: "cuda"
```

**Monitor GPU Usage:**

```bash
# Real-time monitoring
nvidia-smi -l 1

# Python script
python -c "import torch; print(torch.cuda.memory_summary())"
```

**Optimal GPU Memory:**
- YOLOv8n: ~500MB
- YOLOv8s: ~800MB
- YOLOv8m: ~1.5GB

### Model Selection

Trade-off between speed and accuracy:

| Model | Latency | Accuracy | Memory | Recommendation |
|-------|---------|----------|--------|----------------|
| yolov8n.pt | 3ms | Good | 500MB | ✓ Best for 60+ FPS |
| yolov8s.pt | 5ms | Better | 800MB | Balanced |
| yolov8m.pt | 10ms | Excellent | 1.5GB | Use if accuracy issues |
| yolov8l.pt | 20ms | Outstanding | 3GB | Not recommended |

**Change Model:**
```yaml
detection:
  model: "yolov8n.pt"  # Fastest
```

### Input Size Optimization

Lower resolution = faster processing:

```yaml
detection:
  imgsz: 640   # Default
  # imgsz: 416 # Faster, less accurate
  # imgsz: 320 # Fastest, least accurate
```

**Recommendation:** Keep at 640 unless FPS issues.

---

## Camera Settings

### Resolution vs FPS Trade-off

```yaml
camera:
  # High resolution (slower)
  width: 1920
  height: 1080
  fps: 30
  
  # Balanced (recommended)
  width: 1280
  height: 720
  fps: 60
  
  # Low resolution (faster)
  width: 640
  height: 480
  fps: 60
```

**Recommendation:** 1280x720@60fps for best balance

### Buffer Management

Minimize latency with low buffer:

```yaml
camera:
  buffer_size: 1  # Lowest latency (recommended)
  # buffer_size: 2  # Slight stability improvement
```

**Never use buffer_size > 2** - introduces lag

### Backend Selection

```yaml
camera:
  backend: "DSHOW"  # Windows - lowest latency
  # backend: "MSMF"  # Windows - alternative
  # backend: "V4L2"  # Linux
  # backend: "ANY"   # Auto-detect
```

**Performance Comparison:**
- DSHOW (Windows): Fastest, 5-10ms latency
- MSMF (Windows): Moderate, 10-15ms latency
- V4L2 (Linux): Fast, 5-10ms latency

---

## Detection Tuning

### Confidence Threshold

Lower = more detections but more false positives:

```yaml
detection:
  confidence_threshold: 0.45  # Default
  # confidence_threshold: 0.35  # More sensitive
  # confidence_threshold: 0.60  # More selective
```

**Optimization:**
1. Start at 0.45
2. If missing detections → lower to 0.35
3. If false detections → raise to 0.55
4. Monitor in debug mode

### Maximum Detections

Limit for performance:

```yaml
detection:
  max_det: 5  # Usually only 1 ball
  # max_det: 1  # Fastest if single ball
```

---

## Tracking Optimization

### Kalman Filter Tuning

Balance smoothness vs responsiveness:

```yaml
tracking:
  kalman_process_noise: 0.01      # Motion model noise
  kalman_measurement_noise: 0.1   # Sensor noise
```

**High Speed Ball:**
```yaml
kalman_process_noise: 0.05  # More responsive
kalman_measurement_noise: 0.05
```

**Slow/Smooth Ball:**
```yaml
kalman_process_noise: 0.001  # Smoother tracking
kalman_measurement_noise: 0.2
```

### Track Management

```yaml
tracking:
  max_disappear_frames: 10  # Track persistence
  # Lower = faster cleanup, higher = more stable
```

---

## Hit Detection Tuning

### Velocity Threshold

Minimum velocity change for hit:

```yaml
hit_detection:
  velocity_threshold: -50  # Default
  # velocity_threshold: -30  # More sensitive
  # velocity_threshold: -80  # Less sensitive
```

**Too Sensitive:** False hits on slow movements
**Not Sensitive:** Missing soft hits

### Direction Change Angle

```yaml
hit_detection:
  direction_change_angle: 120  # Default
  # direction_change_angle: 90   # More sensitive
  # direction_change_angle: 150  # Less sensitive
```

### Confirmation Frames

```yaml
hit_detection:
  hit_confirmation_frames: 3  # Default
  # hit_confirmation_frames: 1  # Faster response
  # hit_confirmation_frames: 5  # More stable
```

**Trade-off:**
- Lower = faster response, more false positives
- Higher = slower response, fewer false positives

### Debounce Time

Prevent duplicate hits:

```yaml
hit_detection:
  debounce_time: 0.3  # 300ms between hits
  # debounce_time: 0.2  # Faster repeated hits
  # debounce_time: 0.5  # Slower, more stable
```

---

## Network Optimization

### Protocol Selection

**UDP (Recommended):**
- Lowest latency (~1-2ms)
- No connection overhead
- Best for local network

```yaml
network:
  protocol: "udp"
  udp_host: "127.0.0.1"
  udp_port: 9000
```

**WebSocket:**
- Slightly higher latency (~3-5ms)
- Reliable delivery
- Better for remote connection

### Network Latency Testing

**Measure Round-Trip Time:**

```bash
# Vision machine
ping <unity-machine-ip>
```

Target: <1ms for local, <10ms for LAN

**Monitor Packet Loss:**

```bash
# Windows
ping -n 100 <unity-machine-ip>

# Linux
ping -c 100 <unity-machine-ip>
```

Target: 0% packet loss

---

## System-Level Optimization

### Process Priority

**Windows:**

```powershell
# Run vision engine with high priority
Start-Process python -ArgumentList "main.py run" -Priority High
```

**Linux:**

```bash
# Run with nice value -10
nice -n -10 python main.py run
```

### CPU Affinity

Dedicate CPU cores:

**Python:**
```python
import os
os.sched_setaffinity(0, {0, 1, 2, 3})  # Use cores 0-3
```

**Unity:**
Use different cores than vision engine

### Power Settings

**Windows:**
- Control Panel → Power Options
- Select "High Performance"
- Advanced: Set "Processor power management" to 100%

**Linux:**
```bash
sudo cpupower frequency-set -g performance
```

### Disable Background Services

**Windows:**
- Disable Windows Update during sessions
- Close antivirus real-time scanning
- Disable Windows Defender (if safe)
- Close browser, Discord, etc.

**Unity:**
- Disable unnecessary game objects
- Reduce quality settings if needed
- Disable VSync for lowest latency
- Target 60+ FPS in build

---

## Performance Monitoring

### Vision Engine Metrics

**Enable Performance Logging:**

```python
# In main.py, add periodic logging:
if frame_count % 300 == 0:
    performance.log_stats()
```

**Key Metrics:**
- Current FPS: Should be 60+
- Frame Time: Should be <16ms
- GPU Memory: Monitor for leaks
- Frame Drop Rate: Should be <1%

### Unity Metrics

**Profiler:**
1. Window → Analysis → Profiler
2. Monitor:
   - CPU Usage: <70%
   - GPU Usage: <80%
   - Memory: Stable (no leaks)
   - GC Allocations: Minimal

**Stats Window:**
```csharp
// In development build
UnityEngine.Profiling.Profiler.enabled = true;
```

---

## Optimization Checklist

### Before Every Session

- [ ] Close unnecessary applications
- [ ] Set high performance power mode
- [ ] Verify GPU drivers up to date
- [ ] Check camera connection stable
- [ ] Monitor temperatures (GPU <80°C)

### Vision Engine

- [ ] CUDA enabled and working
- [ ] FP16 half-precision enabled
- [ ] YOLOv8n model (fastest)
- [ ] Camera resolution 1280x720 or lower
- [ ] Buffer size = 1
- [ ] imgsz = 640 or lower

### Unity Client

- [ ] VSync disabled (Edit → Project Settings → Quality)
- [ ] Target frame rate unlimited
- [ ] Object pooling enabled
- [ ] Minimal UI updates per frame
- [ ] No debug logging in builds

### Network

- [ ] UDP protocol selected
- [ ] Local network (same subnet)
- [ ] No firewalls blocking
- [ ] <1ms ping time
- [ ] 0% packet loss

---

## Troubleshooting Performance Issues

### Low FPS (<30)

**Diagnose:**
1. Check GPU usage: `nvidia-smi`
2. Check CPU usage: Task Manager/htop
3. Monitor frame times in debug mode

**Solutions:**
1. Enable CUDA if disabled
2. Lower camera resolution
3. Use yolov8n.pt model
4. Reduce imgsz to 416
5. Close background applications
6. Check thermal throttling

### High Latency (>60ms)

**Diagnose:**
1. Measure each component:
   - Camera capture: Check buffer size
   - Detection: Check inference time
   - Network: Ping test
   - Unity: Profiler

**Solutions:**
1. Reduce buffer_size to 1
2. Use UDP instead of WebSocket
3. Lower hit_confirmation_frames
4. Optimize Unity Update() loops
5. Disable VSync in Unity

### Frame Drops (>5%)

**Diagnose:**
```python
stats = camera.get_statistics()
print(f"Drop rate: {stats['drop_rate']:.2f}%")
```

**Solutions:**
1. Increase processing speed (see Low FPS)
2. Reduce max_det to 1
3. Skip frames: Process every 2nd frame
4. Lower camera FPS if detection can't keep up

### Jittery Tracking

**Symptoms:** Ball position jumps around

**Solutions:**
1. Increase kalman_measurement_noise
2. Smooth trajectory (TrajectoryAnalyzer)
3. Increase tracking confidence threshold
4. Improve lighting conditions
5. Use higher confidence_threshold

---

## Advanced Optimization

### Custom YOLO Training

Train on your specific ball and environment:

1. Collect dataset (100+ images)
2. Annotate with Roboflow
3. Train YOLOv8 model
4. Replace yolov8n.pt with custom model

**Benefits:** 
- Higher accuracy
- Lower confidence threshold needed
- Fewer false positives

### Multi-Camera Setup

For larger walls:

1. Use 2+ cameras with overlapping views
2. Run separate vision engine instances
3. Merge detections in Unity
4. Coordinate transform per camera

### Hardware Acceleration

**Intel OpenVINO:**
- CPU-based acceleration
- Alternative to CUDA
- Good for Intel systems

**NVIDIA TensorRT:**
- Further GPU optimization
- ~30% faster than CUDA
- More complex setup

---

## Performance Profiles

### Profile 1: Maximum Performance

```yaml
camera: {width: 640, height: 480, fps: 60}
detection: {model: "yolov8n.pt", imgsz: 416, half_precision: true}
tracking: {max_disappear_frames: 5}
hit_detection: {hit_confirmation_frames: 1}
network: {protocol: "udp"}
```

**Result:** 80+ FPS, <30ms latency

### Profile 2: Balanced

```yaml
camera: {width: 1280, height: 720, fps: 60}
detection: {model: "yolov8n.pt", imgsz: 640, half_precision: true}
tracking: {max_disappear_frames: 10}
hit_detection: {hit_confirmation_frames: 3}
network: {protocol: "udp"}
```

**Result:** 60+ FPS, <40ms latency

### Profile 3: Maximum Quality

```yaml
camera: {width: 1920, height: 1080, fps: 30}
detection: {model: "yolov8s.pt", imgsz: 640, half_precision: true}
tracking: {max_disappear_frames: 15}
hit_detection: {hit_confirmation_frames: 5}
network: {protocol: "websocket"}
```

**Result:** 30+ FPS, <60ms latency
