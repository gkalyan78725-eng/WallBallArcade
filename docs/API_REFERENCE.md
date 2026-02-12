# API Reference

Complete API documentation for the Wall Ball AR Arcade system.

---

## Python Vision Engine API

### Core Module

#### CameraManager

Multi-threaded camera capture manager.

```python
from core import CameraManager

camera = CameraManager(
    camera_index=0,
    width=1280,
    height=720,
    fps=60,
    buffer_size=1,
    backend="DSHOW"
)
```

**Methods:**

```python
# Start camera capture
success = camera.start()

# Get latest frame (non-blocking)
success, frame = camera.get_frame(timeout=0.1)

# Stop camera
camera.stop()

# Get statistics
stats = camera.get_statistics()
# Returns: {total_frames, dropped_frames, drop_rate, avg_fps, elapsed_time}
```

**Context Manager:**

```python
with CameraManager(camera_index=0) as camera:
    success, frame = camera.get_frame()
```

---

#### GPUDetector

YOLO-based object detection with GPU acceleration.

```python
from core import GPUDetector

detector = GPUDetector(
    model_path="yolov8n.pt",
    device="cuda",
    confidence_threshold=0.45,
    iou_threshold=0.4,
    imgsz=640,
    half_precision=True,
    max_det=5
)
```

**Methods:**

```python
# Warmup model
detector.warmup(warmup_frames=30, frame_shape=(720, 1280, 3))

# Detect objects
detections = detector.detect(frame)
# Returns: List[Detection]

# Filter by class
ball_detections = detector.filter_by_class(detections, class_id=32)

# Get performance stats
stats = detector.get_performance_stats()
# Returns: {avg_inference_time, avg_fps, total_detections, device, half_precision}
```

**Detection Class:**

```python
@dataclass
class Detection:
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    confidence: float
    class_id: int
    center: Tuple[float, float]  # (cx, cy)
```

---

#### BallTracker

Kalman filter-based ball tracking.

```python
from core import BallTracker

tracker = BallTracker(
    process_noise=0.01,
    measurement_noise=0.1,
    max_disappear_frames=10,
    min_hit_confidence=0.6,
    trajectory_history_size=30
)
```

**Methods:**

```python
# Initialize tracker
tracker.initialize(position=(x, y), confidence=1.0)

# Update with detection
tracker.update(position=(x, y), confidence=0.9)

# Predict without measurement
tracker.predict()

# Get current state
state = tracker.get_state()
# Returns: TrackState | None

# Predict future position
future_pos = tracker.predict_position(frames_ahead=10)

# Get velocity
speed = tracker.get_velocity_magnitude()
angle = tracker.get_velocity_angle()

# Reset tracker
tracker.reset()
```

**TrackState Class:**

```python
@dataclass
class TrackState:
    position: Tuple[float, float]
    velocity: Tuple[float, float]
    confidence: float
    age: int
    trajectory: List[Tuple[float, float]]
```

---

#### PerformanceMonitor

System performance monitoring.

```python
from core import PerformanceMonitor

monitor = PerformanceMonitor(
    window_size=60,
    target_fps=60
)
```

**Methods:**

```python
# Mark frame start/end
monitor.start_frame()
monitor.end_frame()

# Get metrics
fps = monitor.get_fps()
frame_time = monitor.get_frame_time_ms()
gpu_util = monitor.get_gpu_utilization()
memory = monitor.get_memory_usage()
gpu_memory = monitor.get_gpu_memory()

# Get all stats
stats = monitor.get_overall_stats()

# Check performance
adequate = monitor.is_performance_adequate(threshold=0.8)

# Reset statistics
monitor.reset()

# Log stats
monitor.log_stats()
```

---

### Processing Module

#### HitDetector

Physics-based hit detection.

```python
from processing import HitDetector

detector = HitDetector(
    velocity_threshold=-50,
    direction_change_angle=120,
    hit_confirmation_frames=3,
    min_distance_to_wall=20,
    debounce_time=0.3,
    wall_bounds=(x_min, y_min, x_max, y_max)
)
```

**Methods:**

```python
# Set wall boundaries
detector.set_wall_bounds((0, 0, 1280, 720))

# Check for hit
hit_event = detector.check_hit(
    position=(x, y),
    velocity=(vx, vy),
    confidence=0.9
)
# Returns: HitEvent | None

# Reset detector
detector.reset()
```

**HitEvent Class:**

```python
@dataclass
class HitEvent:
    position: Tuple[float, float]
    velocity: float
    confidence: float
    timestamp: float
    wall_position: Optional[Tuple[float, float]]
```

---

#### TrajectoryAnalyzer

Trajectory analysis and prediction.

```python
from processing import TrajectoryAnalyzer

analyzer = TrajectoryAnalyzer(
    min_points=5,
    polynomial_degree=2,
    smoothing_window=3
)
```

**Methods:**

```python
# Fit trajectory
coeffs = analyzer.fit_trajectory(trajectory)
# Returns: (x_coeffs, y_coeffs) | None

# Predict impact point
impact = analyzer.predict_impact_point(trajectory, wall_y=0)
# Returns: (x, y) | None

# Calculate speed
speed = analyzer.calculate_speed(trajectory, fps=60)
# Returns: float | None

# Smooth trajectory
smoothed = analyzer.smooth_trajectory(trajectory)
# Returns: List[Tuple[float, float]]

# Calculate velocity at point
velocity = analyzer.calculate_velocity_at_point(trajectory, index=10, fps=60)
# Returns: (vx, vy) | None

# Estimate parabolic motion
params = analyzer.estimate_parabolic_motion(trajectory)
# Returns: dict | None
```

---

#### HomographyMapper

Coordinate transformation.

```python
from processing import HomographyMapper

mapper = HomographyMapper()
```

**Methods:**

```python
# Calibrate from points
success = mapper.calibrate(
    camera_points=[(x1, y1), (x2, y2), (x3, y3), (x4, y4)],
    wall_points=[(0, 0), (1920, 0), (1920, 1080), (0, 1080)]
)

# Transform coordinates
wall_pos = mapper.camera_to_wall((x, y))
camera_pos = mapper.wall_to_camera((x, y))

# Batch transform
wall_positions = mapper.batch_transform(points, camera_to_wall=True)

# Check calibration
is_calibrated = mapper.is_calibrated()

# Get/load calibration
data = mapper.get_calibration_data()
success = mapper.load_calibration(data)
```

---

### Network Module

#### UDPSender

UDP message sender.

```python
from network import UDPSender

sender = UDPSender(host="127.0.0.1", port=9000)
```

**Methods:**

```python
# Send hit event
success = sender.send_hit(x=850.5, y=450.2, velocity=125.7, timestamp=None)

# Send generic message
success = sender.send_message({"type": "hit", "x": 850.5, "y": 450.2})

# Get statistics
stats = sender.get_statistics()
# Returns: {messages_sent, errors, error_rate, last_send_time, host, port}

# Close sender
sender.close()
```

**Context Manager:**

```python
with UDPSender() as sender:
    sender.send_hit(x, y, velocity)
```

---

#### WebSocketSender

WebSocket message sender (async).

```python
from network import WebSocketSender

sender = WebSocketSender(uri="ws://localhost:9001")
```

**Methods:**

```python
# Connect (async)
await sender.connect()

# Send hit event (async)
success = await sender.send_hit(x=850.5, y=450.2, velocity=125.7)

# Send message (async)
success = await sender.send_message({"type": "hit", "x": 850.5})

# Get statistics
stats = sender.get_statistics()

# Close (async)
await sender.close()
```

**Context Manager:**

```python
async with WebSocketSender() as sender:
    await sender.send_hit(x, y, velocity)
```

---

### Calibration Module

#### WallCalibrator

Interactive calibration interface.

```python
from calibration import WallCalibrator

calibrator = WallCalibrator(
    wall_width=1920,
    wall_height=1080
)
```

**Methods:**

```python
# Run calibration
result = calibrator.calibrate(frame)
# Returns: (camera_points, wall_points) | None

# Test calibration
calibrator.test_calibration(frame, homography_mapper)

# Visualize grid
display_frame = calibrator.visualize_calibration_grid(frame, camera_points)
```

---

#### ConfigManager

Configuration file management.

```python
from calibration import ConfigManager

config_manager = ConfigManager(config_dir="config")
```

**Methods:**

```python
# Calibration
success = config_manager.save_calibration(data)
data = config_manager.load_calibration()
exists = config_manager.calibration_exists()

# Settings
settings = config_manager.load_settings(file_path)
success = config_manager.save_settings(settings, file_path)
defaults = config_manager.get_default_settings()

# Validation
is_valid = config_manager.validate_settings(settings)

# Merging
merged = config_manager.merge_settings(base, override)
```

---

### Utils Module

#### Logger Setup

```python
from utils import setup_logger

setup_logger(
    level="INFO",
    log_file="vision_engine.log",
    rotation="10 MB",
    retention="1 week",
    colorize=True
)
```

#### DebugVisualizer

Debug visualization overlay.

```python
from utils import DebugVisualizer

visualizer = DebugVisualizer(
    show_bounding_box=True,
    show_trajectory=True,
    show_fps=True,
    show_info=True
)
```

**Methods:**

```python
# Draw detection
frame = visualizer.draw_detection(frame, bbox, confidence, label="Ball")

# Draw trajectory
frame = visualizer.draw_trajectory(frame, trajectory, color=(255, 0, 0))

# Add hit marker
visualizer.add_hit_marker(position, timestamp)

# Draw markers
frame = visualizer.draw_hit_markers(frame, current_time)

# Draw FPS
frame = visualizer.draw_fps(frame, fps, position=(10, 30))

# Draw info panel
frame = visualizer.draw_info_panel(frame, info_dict, position=(10, 70))

# Draw calibration grid
frame = visualizer.draw_calibration_grid(frame, camera_points, grid_lines=10)

# Complete visualization
display_frame = visualizer.create_visualization(
    frame=frame,
    detection=(bbox, confidence, "Ball"),
    trajectory=trajectory,
    fps=60.0,
    info={"Tracking": "Yes"},
    current_time=time.time()
)
```

---

## Unity C# API

### Core

#### GameManager

Singleton game controller.

```csharp
// Access singleton
GameManager.Instance.StartGame(gameModeComponent);

// Properties
GameState currentState = GameManager.Instance.CurrentState;
IGameMode gameMode = GameManager.Instance.CurrentGameMode;
bool isPlaying = GameManager.Instance.IsPlaying;
bool isPaused = GameManager.Instance.IsPaused;

// Methods
void StartGame(MonoBehaviour gameModeComponent);
void PauseGame();
void ResumeGame();
void EndGame();
void ReturnToMenu();
void RestartGame();

// Events
UnityEvent<GameState> OnStateChanged;
UnityEvent<int> OnScoreUpdated;
UnityEvent OnGameStarted;
UnityEvent OnGameEnded;
```

---

#### HitReceiver

Network message receiver.

```csharp
// Configuration
public NetworkProtocol protocol;  // UDP or WebSocket
public int udpPort = 9000;
public string websocketUri;

// Coordinate transform
public bool normalizeCoordinates = true;
public Vector2 worldSize = new Vector2(10f, 10f);
public Vector2 worldOffset = new Vector2(-5f, -5f);

// Events
UnityEvent<Vector2, float> OnHitDetected;

// Methods
int GetMessageCount();
float GetTimeSinceLastHit();
bool IsConnected();
```

---

#### EventBus

Generic event system.

```csharp
// Subscribe
EventBus.Instance.Subscribe<HitEvent>(OnHit);

// Publish
EventBus.Instance.Publish(new HitEvent(pos, vel, time));

// Unsubscribe
EventBus.Instance.Unsubscribe<HitEvent>(OnHit);

// Clear
EventBus.Instance.Clear<HitEvent>();
EventBus.Instance.ClearAll();
```

**Event Types:**

```csharp
public struct HitEvent {
    public Vector2 Position;
    public float Velocity;
    public float Timestamp;
}

public struct ScoreEvent {
    public int Points;
    public int TotalScore;
    public Vector2 Position;
}

public struct ComboEvent {
    public int ComboCount;
    public float Multiplier;
}

public struct GameStateEvent {
    public GameManager.GameState State;
}
```

---

### Managers

#### ScoreManager

Score and combo management.

```csharp
// Methods
void AddScore(int points);
void ResetScore();
int GetScore();
void UpdateCombo();
void ResetCombo();
int GetComboCount();
float GetComboMultiplier();
int GetHighScore();

// Events
UnityEvent<int> OnScoreChanged;
UnityEvent<int, float> OnComboChanged;
UnityEvent<int> OnNewHighScore;
```

---

#### AudioManager

Audio playback management.

```csharp
// Access singleton
AudioManager.Instance.PlaySFX(clip, volumeScale, pitch, position);

// Methods
void PlaySFX(AudioClip clip, float volumeScale = 1f, float pitch = 1f, Vector3? position = null);
void PlaySFX(string clipName, float volumeScale = 1f);
void PlayOneShot(AudioClip clip, float volumeScale = 1f);
void StopAll();

void SetMasterVolume(float volume);
void SetSFXVolume(float volume);
void SetMusicVolume(float volume);
```

---

#### UIManager

UI panel and display management.

```csharp
// Access singleton
UIManager.Instance.UpdateScore(score);

// Methods
void ShowMenu();
void ShowGame();
void ShowPause();
void HidePause();
void ShowGameOver(int finalScore, int highScore);

void UpdateScore(int score);
void UpdateCombo(int comboCount, float multiplier);
void UpdateTimer(float timeRemaining);

// Button handlers
void OnResumeClicked();
void OnRestartClicked();
void OnMenuClicked();
```

---

#### CalibrationManager

Calibration tools and visualization.

```csharp
// Configuration
public bool showCalibrationGrid = false;
public int gridLines = 10;
public Color gridColor = Color.yellow;

public bool testMode = false;
public GameObject hitMarkerPrefab;
```

---

### Game Modes

#### IGameMode Interface

```csharp
public interface IGameMode
{
    void Initialize();
    void OnHit(Vector2 worldPosition, float velocity);
    void Update();
    int GetScore();
    bool IsGameOver();
    void Reset();
}
```

---

#### BrickBreakerMode

```csharp
// Configuration
public GameObject brickPrefab;
public int rows = 5;
public int columns = 10;
public float brickWidth = 0.8f;
public float brickHeight = 0.3f;
public float spacing = 0.1f;

public int pointsPerBrick = 100;
public int bonusPointsTopRow = 50;
public float hitRadius = 0.5f;
```

---

#### TargetShootMode

```csharp
// Configuration
public GameObject targetPrefab;
public int maxActiveTargets = 5;
public float minTargetSize = 0.5f;
public float maxTargetSize = 1.5f;

public float spawnInterval = 2f;
public Vector2 spawnAreaMin;
public Vector2 spawnAreaMax;

public int basePoints = 50;
public int sizeMultiplier = 100;
public float gameDuration = 60f;
```

---

#### ReactionMode

```csharp
// Configuration
public GameObject targetPrefab;
public float minDisplayTime = 0.5f;
public float maxDisplayTime = 2f;
public float timeBetweenTargets = 0.3f;

public int fastHitBonus = 200;
public int mediumHitPoints = 100;
public int slowHitPoints = 50;

public int livesCount = 3;
public int targetCount = 20;
```

---

### Effects

#### HitEffectManager

```csharp
// Access singleton
HitEffectManager.Instance.SpawnHitEffect(position, color);

// Methods
void SpawnHitEffect(Vector3 position, Color? color = null);
void SpawnExplosionEffect(Vector3 position, float scale = 1f);
void SpawnSparkEffect(Vector3 position);
```

---

#### ParticlePooler

```csharp
// Configuration
public GameObject Prefab;
public int PoolSize = 10;
public bool AutoExpand = true;
public float autoReturnTime = 2f;

// Methods
void Initialize();
GameObject Get();
void Return(GameObject obj);
string GetStatistics();
```

---

### Debug

#### DebugOverlay

```csharp
// Configuration
public bool showOnStart = true;
public KeyCode toggleKey = KeyCode.F1;

// Methods
void Show();
void Hide();
void Toggle();
```

---

### Network

#### UDPReceiver

```csharp
// Configuration
public int Port = 9000;

// Events
UnityEvent<string> OnMessageReceived;

// Methods
bool IsListening();
int GetMessageCount();
```

---

#### WebSocketReceiver

```csharp
// Configuration
public string Uri = "ws://localhost:9001";

// Events
UnityEvent<string> OnMessageReceived;
UnityEvent OnConnected;
UnityEvent OnDisconnected;

// Methods
Task ConnectAsync();
void Disconnect();
bool IsConnected();
int GetMessageCount();
```

---

## Network Message Format

### Hit Message (JSON)

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
- `type`: Always "hit"
- `x`: X coordinate (pixels or normalized)
- `y`: Y coordinate (pixels or normalized)
- `velocity`: Hit velocity magnitude
- `timestamp`: Unix timestamp

---

## Configuration Schema

### settings.yaml

```yaml
camera:
  index: int          # Camera device index
  width: int          # Frame width
  height: int         # Frame height
  fps: int            # Target FPS
  buffer_size: int    # Buffer size
  backend: string     # Backend (DSHOW, V4L2, MSMF)

detection:
  model: string       # Model path
  confidence_threshold: float  # 0-1
  iou_threshold: float         # 0-1
  imgsz: int          # Input size
  device: string      # cuda or cpu
  half_precision: bool
  max_det: int

tracking:
  kalman_process_noise: float
  kalman_measurement_noise: float
  max_disappear_frames: int
  min_hit_confidence: float

hit_detection:
  velocity_threshold: float
  direction_change_angle: float
  hit_confirmation_frames: int
  min_distance_to_wall: float
  debounce_time: float

performance:
  target_fps: int
  frame_skip_threshold: float
  warmup_frames: int

network:
  protocol: string    # udp or websocket
  udp_host: string
  udp_port: int
  websocket_uri: string

debug:
  show_visualization: bool
  show_fps: bool
  show_trajectory: bool
  show_bounding_box: bool
  save_debug_video: bool
```

---

## Examples

### Python Example

```python
from core import CameraManager, GPUDetector, BallTracker
from processing import HitDetector, HomographyMapper
from network import UDPSender

# Initialize components
camera = CameraManager(camera_index=0)
detector = GPUDetector()
tracker = BallTracker()
hit_detector = HitDetector()
mapper = HomographyMapper()
sender = UDPSender()

# Load calibration
mapper.load_calibration(calibration_data)

# Start camera
camera.start()

# Main loop
while True:
    # Capture frame
    ret, frame = camera.get_frame()
    if not ret:
        continue
    
    # Detect ball
    detections = detector.detect(frame)
    ball_detections = detector.filter_by_class(detections, 32)
    
    # Track ball
    if ball_detections:
        tracker.update(ball_detections[0].center, ball_detections[0].confidence)
    else:
        tracker.predict()
    
    # Check hit
    state = tracker.get_state()
    if state:
        hit = hit_detector.check_hit(state.position, state.velocity)
        
        if hit:
            # Transform coordinates
            wall_pos = mapper.camera_to_wall(hit.position)
            
            # Send to Unity
            sender.send_hit(wall_pos[0], wall_pos[1], hit.velocity)

camera.stop()
```

### Unity Example

```csharp
using UnityEngine;

public class GameSetup : MonoBehaviour
{
    [SerializeField] private HitReceiver hitReceiver;
    [SerializeField] private BrickBreakerMode brickBreaker;
    
    private void Start()
    {
        // Subscribe to events
        hitReceiver.OnHitDetected.AddListener(OnHitReceived);
        
        // Start game
        GameManager.Instance.StartGame(brickBreaker);
        
        // Subscribe to event bus
        EventBus.Instance.Subscribe<ScoreEvent>(OnScoreChanged);
    }
    
    private void OnHitReceived(Vector2 position, float velocity)
    {
        Debug.Log($"Hit at {position} with velocity {velocity}");
        
        // Spawn effect
        if (HitEffectManager.Instance != null)
        {
            HitEffectManager.Instance.SpawnHitEffect(position);
        }
    }
    
    private void OnScoreChanged(ScoreEvent evt)
    {
        Debug.Log($"Score: {evt.TotalScore} (+{evt.Points})");
    }
    
    private void OnDestroy()
    {
        hitReceiver.OnHitDetected.RemoveListener(OnHitReceived);
        EventBus.Instance.Unsubscribe<ScoreEvent>(OnScoreChanged);
    }
}
```
