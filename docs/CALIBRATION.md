# Calibration Guide

Complete guide to calibrating the Wall Ball AR Arcade system for accurate coordinate mapping.

---

## Overview

Calibration maps camera coordinates to wall/projector coordinates using homography transformation. This is essential for accurate hit detection in the game world.

**What is Homography?**
A mathematical transformation that maps points from one plane (camera view) to another plane (wall surface) using a 3x3 matrix.

---

## Physical Setup

### 1. Equipment Positioning

**Camera Placement:**
- Mount at eye level or slightly above
- Position to capture entire projection area
- Avoid extreme angles (>45° from perpendicular)
- Minimize lens distortion (use center of frame)
- Ensure stable mounting (no vibration)

**Optimal Camera Position:**
```
        Camera
          |
          | 3-5m
          |
          ↓
    ================
    |              |
    |     Wall     |  ← Projection surface
    |              |
    ================
```

**Projector Setup:**
- Mount securely
- Project onto flat wall
- Ensure image fills wall evenly
- Correct keystone distortion
- Lock focus and zoom

**Wall Requirements:**
- Flat surface (no curves/bumps)
- Uniform color (white preferred)
- Good contrast with ball
- No reflective materials
- Adequate size (2m x 2m minimum)

### 2. Lighting Conditions

**Ideal Lighting:**
- Bright, even illumination
- No direct sunlight on wall
- Avoid harsh shadows
- Consistent lighting during play
- No backlighting behind ball

**Problem Lighting:**
- ❌ Direct sunlight (overexposure)
- ❌ Dim lighting (poor detection)
- ❌ Spotlights (harsh shadows)
- ❌ Flickering lights (unstable detection)

### 3. Environmental Factors

**Minimize:**
- Moving objects in background
- Reflective surfaces
- Windows with changing light
- Vibrations (from floor, wall)

---

## Calibration Process

### Step 1: Start Calibration

```bash
cd vision_engine
python main.py calibrate --camera 0 --wall-width 1920 --wall-height 1080
```

**Parameters:**
- `--camera 0`: Camera device index
- `--wall-width 1920`: Projector width in pixels
- `--wall-height 1080`: Projector height in pixels

### Step 2: Select Calibration Points

**Window appears showing camera view.**

**Instructions:**
1. Click 4 corners in this order:
   - **Top-Left** (red dot)
   - **Top-Right** (green dot)
   - **Bottom-Right** (blue dot)
   - **Bottom-Left** (cyan dot)

**Visualization:**
```
TL────────────TR
 │            │
 │   Wall     │
 │            │
BL────────────BR
```

**Tips:**
- Click precisely on corner edges
- Use zoom if needed (mouse wheel)
- Points will connect with lines
- Review before accepting

**Keyboard Controls:**
- `r` - Reset points (start over)
- `q` - Cancel calibration
- Auto-accepts after 4 points

### Step 3: Computation

System automatically:
1. Computes homography matrix using RANSAC
2. Calculates reprojection error
3. Validates transformation
4. Saves to `calibration.json`

**Output:**
```
Homography calibrated (error: 2.31 pixels)
Calibration saved to vision_engine/config/calibration.json
```

**Acceptable Error:**
- <2 pixels: Excellent
- 2-5 pixels: Good
- 5-10 pixels: Acceptable
- >10 pixels: Recalibrate

### Step 4: Validation

**Test Mode:**
```bash
python main.py calibrate --camera 0 --test
```

**Process:**
1. Camera view appears
2. Click anywhere on screen
3. See transformed coordinates
4. Verify accuracy

**Validation Checklist:**
- [ ] Click center → Should be near (960, 540)
- [ ] Click top-left → Should be near (0, 0)
- [ ] Click bottom-right → Should be near (1920, 1080)
- [ ] Click multiple points → Check consistency

---

## Calibration Best Practices

### Accuracy Tips

1. **Use Calibration Target:**
   - Display grid pattern on wall
   - Align projected corners precisely
   - Use corner markers

2. **Multiple Captures:**
   - Calibrate 3 times
   - Use best result (lowest error)
   - Average if consistent

3. **Point Selection:**
   - Be precise (use maximum zoom)
   - Select actual corner pixels
   - Avoid approximate clicks

4. **Camera Settings:**
   - Auto-focus OFF (if possible)
   - Lock exposure
   - Disable auto white balance
   - Maximum resolution

### Common Mistakes

❌ **Clicking Inside Corners**
- Effect: Shrinks mapped area
- Fix: Click exact edge pixels

❌ **Wrong Point Order**
- Effect: Distorted mapping
- Fix: Follow TL→TR→BR→BL order

❌ **Camera Moved After Calibration**
- Effect: Mapping invalid
- Fix: Recalibrate after any camera movement

❌ **Non-Planar Wall**
- Effect: High reprojection error
- Fix: Use flat wall, correct warping

❌ **Poor Lighting**
- Effect: Inconsistent detection
- Fix: Improve lighting before calibrating

---

## Advanced Calibration

### Grid-Based Calibration

For higher accuracy:

1. **Project Checkerboard Pattern:**
   - 10x10 grid on wall
   - High contrast (black/white)
   - Known dimensions

2. **Detect Corners:**
   ```python
   import cv2
   ret, corners = cv2.findChessboardCorners(frame, (10, 10))
   ```

3. **Compute Homography:**
   - Use all corner points
   - More stable than 4-point
   - Lower reprojection error

### Multi-Region Calibration

For non-planar surfaces:

1. Divide wall into regions (2x2 grid)
2. Calibrate each region separately
3. Use nearest region for each hit
4. Blend at boundaries

### Dynamic Calibration

Auto-adjust during runtime:

1. Track known reference points
2. Update homography incrementally
3. Compensate for camera drift
4. Requires static markers on wall

---

## Recalibration

### When to Recalibrate

**Required:**
- Camera moved or adjusted
- Projector moved
- Wall/surface changed
- High error rate in validation

**Recommended:**
- Weekly for permanent setups
- Daily for portable setups
- After system restart
- After any hardware changes

### Quick Recalibration

For minor adjustments:

1. Load previous calibration
2. Test with validation mode
3. If error < 5 pixels, keep it
4. Otherwise, full recalibration

---

## Calibration File

### File Location
```
vision_engine/config/calibration.json
```

### File Format
```json
{
  "homography_matrix": [
    [1.23, 0.01, -45.2],
    [0.02, 1.19, -32.1],
    [0.0001, 0.0002, 1.0]
  ],
  "camera_points": [
    [120, 80],
    [1180, 75],
    [1190, 680],
    [110, 690]
  ],
  "wall_points": [
    [0, 0],
    [1919, 0],
    [1919, 1079],
    [0, 1079]
  ],
  "reprojection_error": 2.31
}
```

### Backup and Restore

**Backup:**
```bash
cp config/calibration.json config/calibration_backup_$(date +%Y%m%d).json
```

**Restore:**
```bash
cp config/calibration_backup_20240101.json config/calibration.json
```

---

## Troubleshooting

### High Reprojection Error (>10 pixels)

**Causes:**
1. Inaccurate point selection
2. Non-planar wall surface
3. Lens distortion
4. Camera/projector not aligned

**Solutions:**
1. Recalibrate with more precision
2. Use lens distortion correction
3. Improve wall flatness
4. Adjust camera angle

### Inconsistent Mapping

**Symptoms:** Same physical point maps to different coordinates

**Causes:**
1. Camera auto-focus enabled
2. Camera vibration
3. Changing lighting
4. Thermal drift

**Solutions:**
1. Disable auto-focus
2. Secure camera mount
3. Stabilize lighting
4. Wait for equipment warmup

### Edge Detection Issues

**Symptoms:** Hits not detected near edges

**Causes:**
1. Calibration points too conservative
2. Camera view cuts off wall edges
3. Lens distortion at edges

**Solutions:**
1. Click closer to actual edges
2. Widen camera field of view
3. Use lens correction

### Coordinate Inversion

**Symptoms:** X or Y coordinates inverted

**Causes:**
1. Wrong point order
2. Camera mounted upside down
3. Inverted axes in configuration

**Solutions:**
1. Recalibrate in correct order
2. Rotate camera properly
3. Check coordinate system

---

## Validation Procedures

### Geometric Validation

Test mapping with known points:

```python
def validate_calibration(mapper):
    test_points = [
        ((0, 0), "Top-Left"),
        ((1920, 0), "Top-Right"),
        ((1920, 1080), "Bottom-Right"),
        ((0, 1080), "Bottom-Left"),
        ((960, 540), "Center")
    ]
    
    for wall_point, label in test_points:
        camera_point = mapper.wall_to_camera(wall_point)
        back_to_wall = mapper.camera_to_wall(camera_point)
        error = distance(wall_point, back_to_wall)
        print(f"{label}: error = {error:.2f} pixels")
```

### Physical Validation

1. Mark physical points on wall (tape)
2. Throw ball at each mark
3. Compare detected position vs expected
4. Error should be <50mm

### Runtime Validation

Monitor during gameplay:

1. Enable debug visualization
2. Verify hits align with physical impacts
3. Check hit clustering (should be tight)
4. Recalibrate if drift detected

---

## Calibration Optimization

### Minimize Reprojection Error

1. Use high-resolution calibration
2. Select points with subpixel accuracy
3. Ensure planar wall surface
4. Correct lens distortion first

### Maximize Robustness

1. Test under all lighting conditions
2. Validate at all hit areas
3. Use safety margins (10% padding)
4. Monitor drift over time

### Automate Calibration

For frequent recalibration:

```python
# Auto-detect calibration pattern
def auto_calibrate(frame):
    # Detect ArUco markers or checkerboard
    corners = detect_corners(frame)
    
    # Compute homography
    mapper = HomographyMapper()
    mapper.calibrate(corners, wall_points)
    
    return mapper
```

---

## Summary Checklist

### Pre-Calibration
- [ ] Camera mounted securely
- [ ] Projector aligned and stable
- [ ] Wall flat and clean
- [ ] Lighting consistent and adequate
- [ ] Equipment warmed up (15+ minutes)

### Calibration Process
- [ ] Correct camera index selected
- [ ] Wall dimensions accurate
- [ ] Points selected precisely in order
- [ ] Reprojection error <5 pixels
- [ ] Validation test successful

### Post-Calibration
- [ ] Calibration file backed up
- [ ] Test mode validation passed
- [ ] Integration test with Unity
- [ ] Physical hit test successful
- [ ] Documentation updated

---

## Next Steps

After successful calibration:
- Run full system test: `python main.py test`
- Test with Unity client
- Perform physical hit tests
- Document calibration date and settings
- Set recalibration schedule
