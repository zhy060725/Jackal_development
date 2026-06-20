import importlib

from my_robot_package.semantic_planner import Detection


def capture_and_predict(detector):
    capture_rgb, capture_depth, masked_depth = detector.capture()
    capture_result = detector.predict(capture_rgb, capture_depth)
    return capture_result, masked_depth


def create_detector(
    module_name="RealsenseYolo",
    class_name="RealSenseYOLODetector",
    detector_kwargs=None,
    model_path=None,
):
    module = importlib.import_module(module_name)
    detector_class = getattr(module, class_name)
    kwargs = dict(detector_kwargs or {})
    if model_path:
        kwargs["model_path"] = model_path
    return detector_class(**kwargs)


def normalize_detections(grouped_detections):
    normalized = []
    for fallback_label, objects in (grouped_detections or {}).items():
        for item in objects:
            centroid = getattr(item, "centroid_3d", None)
            if not centroid or len(centroid) != 3:
                continue
            x, y, z = centroid
            if float(x) == 0.0 and float(y) == 0.0 and float(z) == 0.0:
                continue
            detection = Detection(
                label=getattr(item, "label", fallback_label),
                confidence=getattr(item, "confidence", 0.0),
                x=x,
                y=y,
                z=z,
            )
            if detection.has_valid_depth:
                normalized.append(detection)
    return normalized
