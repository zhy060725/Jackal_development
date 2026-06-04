# RealSenseYOLODetector

Captures aligned RGBD frames from an Intel RealSense camera, runs a custom YOLO model, and returns images with detected object locations in 3D space.

## Installation

```bash
pip install pyrealsense2 ultralytics numpy
```

---

## Quick Start

```python
from detector import RealSenseYOLODetector

with RealSenseYOLODetector("best.pt") as detector:
    result = detector.capture()
```

---

## Constructor

```python
RealSenseYOLODetector(
    model_path,
    confidence_threshold=0.5,
    color_resolution=(640, 480),
    depth_resolution=(640, 480),
    fps=30
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `model_path` | `str` | — | Path to your `.pt` YOLO weights file |
| `confidence_threshold` | `float` | `0.5` | Minimum detection confidence (0–1) |
| `color_resolution` | `tuple[int, int]` | `(640, 480)` | Color stream width × height in pixels |
| `depth_resolution` | `tuple[int, int]` | `(640, 480)` | Depth stream width × height in pixels |
| `fps` | `int` | `30` | Frame rate for both streams |

---

## Methods

### `start()` / `stop()`

Manually start or stop the RealSense pipeline.

```python
detector = RealSenseYOLODetector("best.pt")
detector.start()
result = detector.capture()
detector.stop()
```

Prefer the context manager (`with` block) over manual start/stop — it guarantees `stop()` is called even if an exception occurs.

### `capture() → CaptureResult`

Grabs one aligned RGBD frame, runs YOLO detection, and returns a `CaptureResult`.

```python
result = detector.capture()

result.color_image   # np.ndarray, shape (H, W, 3), BGR
result.depth_image   # np.ndarray, shape (H, W), uint16, raw depth units
result.detections    # dict[str, list[DetectedObject]]
```

---

## Return Types

### `CaptureResult`

| Field | Type | Description |
|---|---|---|
| `color_image` | `np.ndarray` | BGR color frame |
| `depth_image` | `np.ndarray` | Raw depth frame (convert with depth scale) |
| `detections` | `dict[str, list[DetectedObject]]` | Detections grouped by label |

### `DetectedObject`

| Field | Type | Description |
|---|---|---|
| `label` | `str` | Class name (e.g. `"cup"`) |
| `confidence` | `float` | Detection confidence (0–1) |
| `bbox_2d` | `tuple[int, int, int, int]` | Bounding box `(x1, y1, x2, y2)` in pixels |
| `centroid_2d` | `tuple[int, int]` | Centroid `(cx, cy)` in pixels |
| `centroid_3d` | `tuple[float, float, float]` | 3D position `(x, y, z)` in metres |

---

## Examples

### Single capture

```python
with RealSenseYOLODetector("best.pt", confidence_threshold=0.6) as detector:
    result = detector.capture()

    for label, objects in result.detections.items():
        for obj in objects:
            print(f"{label}: {obj.centroid_3d}m  (conf={obj.confidence:.2f})")
```

### Continuous capture loop

```python
with RealSenseYOLODetector("best.pt") as detector:
    while True:
        result = detector.capture()

        cups = result.detections.get("cup", [])
        if cups:
            nearest = min(cups, key=lambda o: o.centroid_3d[2])
            print(f"Nearest cup at z={nearest.centroid_3d[2]:.2f}m")
```

### Access raw images

```python
import cv2

with RealSenseYOLODetector("best.pt") as detector:
    result = detector.capture()
    cv2.imshow("Color", result.color_image)
    cv2.waitKey(0)
```

---

## Notes

- `centroid_3d` returns `(0.0, 0.0, 0.0)` when depth is invalid (e.g. out of range or occluded).
- Depth is aligned to the color frame automatically — no manual offset needed.
- For more robust depth at the centroid, average over a small pixel window (e.g. 5×5) before projecting.
