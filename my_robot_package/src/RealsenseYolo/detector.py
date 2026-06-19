import cv2
import numpy as np
import pyrealsense2 as rs
from ultralytics import YOLO


class DetectedObject:
    def __init__(self, label, confidence, bbox_2d, centroid_2d, centroid_3d):
        self.label = label
        self.confidence = confidence
        self.bbox_2d = bbox_2d
        self.centroid_2d = centroid_2d
        self.centroid_3d = centroid_3d


class CaptureResult:
    def __init__(self, color_image, depth_image, detections=None):
        self.color_image = color_image
        self.depth_image = depth_image
        self.detections = detections if detections is not None else {}


class RealSenseYOLODetector:
    GREEN_LOWER1 = np.array([35, 40, 40])
    GREEN_UPPER1 = np.array([85, 255, 255])
    GREEN_LOWER2 = np.array([85, 40, 40])
    GREEN_UPPER2 = np.array([95, 255, 255])

    def __init__(
        self,
        model_path,
        confidence_threshold=0.5,
        color_resolution=(640, 480),
        depth_resolution=(640, 480),
        fps=30,
        enable_green_detection=True,
        min_green_area=5000,
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.color_resolution = color_resolution
        self.depth_resolution = depth_resolution
        self.fps = fps
        self.enable_green_detection = enable_green_detection
        self.min_green_area = min_green_area

        self.model = YOLO(model_path)

        self._green_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        self.pipeline = None
        self.align = None
        self.depth_scale = None
        self.color_intrinsics = None

    def start(self):
        self.pipeline = rs.pipeline()
        config = rs.config()

        config.enable_stream(
            rs.stream.color,
            self.color_resolution[0],
            self.color_resolution[1],
            rs.format.bgr8,
            self.fps,
        )
        config.enable_stream(
            rs.stream.depth,
            self.depth_resolution[0],
            self.depth_resolution[1],
            rs.format.z16,
            self.fps,
        )

        profile = self.pipeline.start(config)

        depth_sensor = profile.get_device().first_depth_sensor()
        self.depth_scale = depth_sensor.get_depth_scale()

        self.align = rs.align(rs.stream.color)

        color_stream = profile.get_stream(rs.stream.color)
        self.color_intrinsics = color_stream.as_video_stream_profile().get_intrinsics()

    def stop(self):
        if self.pipeline is not None:
            self.pipeline.stop()
            self.pipeline = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

    def capture(self):
        frames = self.pipeline.wait_for_frames()
        aligned = self.align.process(frames)

        color_frame = aligned.get_color_frame()
        depth_frame = aligned.get_depth_frame()

        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())

        results = self.model(color_image, conf=self.confidence_threshold, verbose=False)

        detections = {}
        names = self.model.names

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                confidence = float(box.conf[0].cpu().numpy().item())
                cls_id = int(box.cls[0].cpu().numpy().item())
                label = names[cls_id]

                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2

                centroid_3d = self._project_to_3d(cx, cy, depth_frame)

                obj = DetectedObject(
                    label=label,
                    confidence=confidence,
                    bbox_2d=(x1, y1, x2, y2),
                    centroid_2d=(cx, cy),
                    centroid_3d=centroid_3d,
                )
                detections.setdefault(label, []).append(obj)

        if self.enable_green_detection:
            green_objects = self._detect_green(color_image, depth_frame)
            if green_objects:
                detections.setdefault("green", []).extend(green_objects)

        return CaptureResult(
            color_image=color_image,
            depth_image=depth_image,
            detections=detections,
        )

    def _detect_green(self, color_image, depth_frame):
        hsv = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)

        mask1 = cv2.inRange(hsv, self.GREEN_LOWER1, self.GREEN_UPPER1)
        mask2 = cv2.inRange(hsv, self.GREEN_LOWER2, self.GREEN_UPPER2)
        green_mask = cv2.bitwise_or(mask1, mask2)

        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, self._green_kernel, iterations=3)
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, self._green_kernel, iterations=2)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(green_mask, connectivity=8)

        objects = []
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < self.min_green_area:
                continue

            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]

            cx = x + w // 2
            cy = y + h // 2

            centroid_3d = self._project_to_3d(cx, cy, depth_frame)

            obj = DetectedObject(
                label="green",
                confidence=1.0,
                bbox_2d=(x, y, x + w, y + h),
                centroid_2d=(cx, cy),
                centroid_3d=centroid_3d,
            )
            objects.append(obj)

        return objects

    def _project_to_3d(self, cx, cy, depth_frame):
        h = self.color_intrinsics.height
        w = self.color_intrinsics.width
        if not (0 <= cx < w and 0 <= cy < h):
            return 0.0, 0.0, 0.0

        depth = depth_frame.get_distance(cx, cy)
        if depth <= 0.0:
            return 0.0, 0.0, 0.0

        point = rs.rs2_deproject_pixel_to_point(
            self.color_intrinsics, [float(cx), float(cy)], depth
        )
        return float(point[0]), float(point[1]), float(point[2])