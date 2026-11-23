from typing import NotRequired, TypedDict
from pathlib import Path


IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png"]


class DetectionBoudingBoxes(TypedDict):
    bboxes: list[tuple[float, float, float, float]]
    canvas_size: tuple[int, int]
    labels: NotRequired[list[str]]
    indexes: NotRequired[list[int]]


def scale_detection(
    detection: DetectionBoudingBoxes,
    canvas_size: tuple[int, int],
) -> DetectionBoudingBoxes:
    w_scale = canvas_size[0] / detection["canvas_size"][0]
    h_scale = canvas_size[1] / detection["canvas_size"][1]
    scaled_detec = {
        "bboxes": [
            (x * w_scale, y * h_scale, w * w_scale, h * h_scale)
            for (x, y, w, h) in detection["bboxes"]
        ],
        "canvas_size": canvas_size,
    }
    for key in ("labels", "indexes"):
        try:
            scaled_detec[key] = detection[key]
        except KeyError:
            continue
    return scaled_detec


def crop_detection(
    detection: DetectionBoudingBoxes,
    left: int,
    top: int,
    right: int,
    bottom: int,
    min_box_width: float = 5.0,
    min_box_height: float = 5.0,
):
    bboxes = []
    selection = []
    for i, bbox in enumerate(detection["bboxes"]):
        x1 = bbox[0] - bbox[2] / 2
        y1 = bbox[1] - bbox[3] / 2
        x2 = min(right, x1 + bbox[2])
        y2 = min(bottom, y1 + bbox[3])
        x1 = max(left, x1)
        y1 = max(top, y1)
        if x1 >= (x2 - min_box_width) or y1 >= (y2 - min_box_height):
            continue
        selection.append(i)
        bboxes.append(
            (
                (x1 + x2) / 2 - left,
                (y1 + y2) / 2 - top,
                x2 - x1,
                y2 - y1,
            )
        )
    cropped_detec = {
        "bboxes": bboxes,
        "canvas_size": (right - left, bottom - top),
    }
    for key in ("labels", "indexes"):
        try:
            value = detection[key]
            cropped_detec[key] = [value[i] for i in selection]
        except KeyError:
            continue
    return cropped_detec


def list_images_in_directory(
    target_directory: str | Path,
    extensions: list[str] = None,
):
    extensions = frozenset(
        IMAGE_EXTENSIONS if extensions is None else extensions
    )
    return [
        item
        for item in Path(target_directory).iterdir()
        if item.suffix in extensions
    ]
