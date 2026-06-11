import pathlib
import sys
import types


PACKAGE_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from my_robot_package.yolo_capture_adapter import create_detector, normalize_detections


class FakeObject(object):
    def __init__(self, label, confidence, centroid_3d):
        self.label = label
        self.confidence = confidence
        self.centroid_3d = centroid_3d


def test_normalize_flattens_grouped_detections():
    grouped = {
        "car": [FakeObject("car", 0.9, (0.2, 0.0, 2.0))],
        "cone": [FakeObject("cone", 0.8, (-0.3, 0.0, 1.0))],
    }

    detections = normalize_detections(grouped)

    assert [(item.label, item.x, item.z) for item in detections] == [
        ("car", 0.2, 2.0),
        ("cone", -0.3, 1.0),
    ]


def test_normalize_drops_invalid_zero_depth():
    grouped = {"car": [FakeObject("car", 0.9, (0.0, 0.0, 0.0))]}

    assert normalize_detections(grouped) == []


def test_create_detector_imports_class_with_model_path(monkeypatch):
    module = types.ModuleType("fake_yolo_capture")

    class FakeDetector(object):
        def __init__(self, model_path, confidence_threshold=0.5):
            self.model_path = model_path
            self.confidence_threshold = confidence_threshold

    module.RealSenseYOLODetector = FakeDetector
    monkeypatch.setitem(sys.modules, "fake_yolo_capture", module)

    detector = create_detector(
        module_name="fake_yolo_capture",
        class_name="RealSenseYOLODetector",
        detector_kwargs={"confidence_threshold": 0.7},
        model_path="/tmp/best.pt",
    )

    assert isinstance(detector, FakeDetector)
    assert detector.model_path == "/tmp/best.pt"
    assert detector.confidence_threshold == 0.7
