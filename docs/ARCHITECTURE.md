# System Architecture

## Overview

The Wall Ball AR Arcade system consists of two main components:

1. **Vision Engine (Python)** - Real-time ball detection and hit processing
2. **Unity Client (C#)** - Game logic, visualization, and user interface

These components communicate via UDP or WebSocket protocols to achieve low-latency (&lt;40ms) end-to-end performance.

---

## Vision Engine Architecture

### Component Hierarchy

```
vision_engine/
├── core/                    # Core processing components
│   ├── CameraManager        # Multi-threaded camera capture
│   ├── GPUDetector          # YOLO-based ball detection
│   ├── BallTracker          # Kalman filter tracking
│   └── PerformanceMonitor   # FPS and resource monitoring
├── processing/              # Hit detection and analysis
│   ├── HitDetector          # Physics-based hit detection
│   ├── TrajectoryAnalyzer   # Trajectory analysis
│   └── HomographyMapper     # Coordinate transformation
├── calibration/             # Setup and calibration
│   ├── WallCalibrator       # Interactive calibration
│   └── ConfigManager        # Configuration management
├── network/                 # Communication
│   ├── UDPSender           # UDP protocol
│   └── WebSocketSender     # WebSocket protocol
└── utils/                   # Utilities
    ├── Logger              # Structured logging
    └── DebugVisualizer     # Debug visualization
```

### Threading Model

The vision engine uses multiple threads for optimal performance:

1. **Main Thread** - Coordinates all components, runs main loop
2. **Camera Thread** - Continuous frame capture (CameraManager)
3. **Network Thread** - Async UDP/WebSocket sending (optional)

**Thread Safety:**
- Frame queue with locks in CameraManager
- Thread-safe message queue in network senders
- No shared mutable state between threads

### Data Flow

```
Camera → Detection → Tracking → Hit Detection → Network
  ↓         ↓          ↓            ↓              ↓
Queue    GPU/YOLO   Kalman      Physics      UDP/WebSocket
  ↓         ↓          ↓            ↓              ↓
Main    Bounding   Position/   HitEvent      Unity
Thread    Boxes    Velocity    w/Transform   Client
```

**Detailed Flow:**

1. **CameraManager** captures frames in background thread → queue
2. **Main loop** retrieves latest frame from queue
3. **GPUDetector** runs YOLOv8 inference → detections
4. **BallTracker** updates Kalman filter with detection → track state
5. **HitDetector** analyzes velocity/direction changes → hit event
6. **HomographyMapper** transforms coordinates → wall space
7. **UDPSender/WebSocketSender** transmits event → Unity

---

## Unity Client Architecture

### Component Hierarchy

```
unity_client/
├── Core/
│   ├── GameManager         # Singleton game controller
│   ├── HitReceiver         # Network message receiver
│   └── EventBus            # Event system
├── Managers/
│   ├── ScoreManager        # Scoring and combos
│   ├── AudioManager        # Audio playback
│   ├── UIManager           # UI display
│   └── CalibrationManager  # Calibration tools
├── Games/
│   ├── IGameMode          # Game mode interface
│   ├── BrickBreakerMode   # Brick breaker game
│   ├── TargetShootMode    # Target shooting game
│   └── ReactionMode       # Reaction timing game
├── Effects/
│   ├── HitEffectManager   # Particle effects
│   └── ParticlePooler     # Object pooling
├── Debug/
│   └── DebugOverlay       # Development tools
└── Network/
    ├── UDPReceiver        # UDP protocol
    └── WebSocketReceiver  # WebSocket protocol
```

### Game State Machine

```
┌──────┐
│ Menu │
└──┬───┘
   │ StartGame()
   ↓
┌─────────┐  PauseGame()  ┌────────┐
│ Playing ├──────────────→│ Paused │
└────┬────┘               └───┬────┘
     │                        │
     │ EndGame()   ResumeGame()│
     ↓                        ↓
┌──────────┐              ┌─────────┐
│ GameOver │              │ Playing │
└─────┬────┘              └─────────┘
      │
      │ ReturnToMenu()
      ↓
   ┌──────┐
   │ Menu │
   └──────┘
```

### Event System

The system uses **EventBus** for decoupled communication:

**Event Types:**
- `HitEvent` - Ball hit detected
- `ScoreEvent` - Score changed
- `ComboEvent` - Combo changed
- `GameStateEvent` - Game state changed
- `GameOverEvent` - Game ended
- `LevelCompleteEvent` - Level completed

**Usage Pattern:**
```csharp
// Subscribe
EventBus.Instance.Subscribe<HitEvent>(OnHit);

// Publish
EventBus.Instance.Publish(new HitEvent(position, velocity, time));

// Unsubscribe
EventBus.Instance.Unsubscribe<HitEvent>(OnHit);
```

---

## Network Protocol

### Message Format (JSON)

```json
{
    "type": "hit",
    "x": 850.5,
    "y": 450.2,
    "velocity": 125.7,
    "timestamp": 1234567890.123
}
```

**Fields:**
- `type`: Message type (always "hit")
- `x`: X coordinate in wall space (pixels)
- `y`: Y coordinate in wall space (pixels)
- `velocity`: Hit velocity magnitude (pixels/sec)
- `timestamp`: Unix timestamp (seconds)

### Protocols

#### UDP
- **Port:** 9000 (configurable)
- **Advantages:** Low latency, no connection overhead
- **Disadvantages:** No delivery guarantee
- **Use case:** Local network, low packet loss

#### WebSocket
- **URI:** ws://localhost:9001 (configurable)
- **Advantages:** Reliable delivery, connection status
- **Disadvantages:** Slightly higher latency
- **Use case:** Remote connection, need reliability

---

## Calibration Process

### 4-Point Homography Calibration

**Purpose:** Map camera coordinates to projector/wall coordinates

**Process:**
1. Display camera feed
2. User clicks 4 wall corners in order:
   - Top-left
   - Top-right
   - Bottom-right
   - Bottom-left
3. Compute homography matrix using RANSAC
4. Save calibration to `calibration.json`

**Homography Transform:**

```python
# Camera point (xc, yc) → Wall point (xw, yw)
[xw]   [h11 h12 h13]   [xc]
[yw] = [h21 h22 h23] × [yc]
[1 ]   [h31 h32 h33]   [1 ]
```

**Validation:**
- Reprojection error calculated
- Test mode for visual validation
- Grid overlay for verification

---

## Performance Optimization

### Target Performance
- **Vision Engine FPS:** 60+ FPS
- **Detection Latency:** &lt;15ms per frame
- **Network Latency:** &lt;5ms
- **Total Latency:** &lt;40ms end-to-end

### Optimization Strategies

#### Vision Engine
1. **GPU Acceleration**
   - CUDA for YOLO inference
   - FP16 half-precision (2x speedup)
   - Batch size 1 for minimal latency

2. **Multi-threading**
   - Separate camera capture thread
   - Frame queue with size 2
   - Automatic frame dropping when busy

3. **Frame Management**
   - Low camera buffer (1 frame)
   - Queue-based latest frame retrieval
   - Skip frames if processing too slow

#### Unity Client
1. **Object Pooling**
   - Particle systems pooled
   - Prefab instantiation minimized
   - Auto-return mechanism

2. **Update Optimization**
   - Physics calculations only when needed
   - Spatial partitioning for hit detection
   - Batch UI updates

3. **Memory Management**
   - No allocations in hot paths
   - Struct-based events (no GC)
   - Cached component references

---

## Error Handling

### Vision Engine
- Try/except blocks around I/O operations
- Graceful degradation (CPU fallback if no GPU)
- Logging all errors with context
- Automatic reconnection for network

### Unity Client
- Null checks before component access
- Try/catch in network receive threads
- Fallback to default values on error
- Debug overlay for troubleshooting

---

## Security Considerations

1. **Network Security**
   - Local network only (no internet exposure)
   - No authentication (trusted environment)
   - No sensitive data transmitted

2. **Input Validation**
   - JSON parsing with error handling
   - Coordinate bounds checking
   - Sanity checks on velocity values

3. **Resource Limits**
   - Maximum queue sizes
   - Frame dropping under load
   - Memory pooling with limits

---

## Extension Points

### Adding New Game Modes

1. Implement `IGameMode` interface
2. Register with GameManager
3. Handle hit events
4. Manage game state

### Adding New Network Protocols

1. Implement sender in vision engine
2. Implement receiver in Unity
3. Add protocol selection in config
4. Update HitReceiver dispatcher

### Adding New Visualization

1. Add overlay to DebugVisualizer
2. Subscribe to relevant events
3. Toggle with configuration
4. Optimize for performance
