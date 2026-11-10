from typing import TypedDict


class DetectionBoudingBoxes(TypedDict):
    bboxes: list[tuple[float, float, float, float]]
    labels: list[str]
    canvas_size: tuple[int, int]


def scale_detection(
    detection: DetectionBoudingBoxes,
    canvas_size: tuple[int, int],
) -> DetectionBoudingBoxes:
    w_scale = canvas_size[0] / detection["canvas_size"][0]
    h_scale = canvas_size[1] / detection["canvas_size"][1]
    detection["bboxes"] = [
        (x * w_scale, y * h_scale, w * w_scale, h * h_scale)
        for (x, y, w, h) in detection["bboxes"]
    ]
    detection["canvas_size"] = canvas_size
    return detection


def crop_detection(
    detection: DetectionBoudingBoxes,
    left: int,
    top: int,
    right: int,
    bottom: int,
    min_box_width: int = 5,
    min_box_height: int = 5,
):
    bboxes = []
    labels = []
    for label, bbox in zip(detection["labels"], detection["bboxes"]):
        x1 = bbox[0] - bbox[2] / 2
        y1 = bbox[1] - bbox[3] / 2
        x2 = min(right, x1 + bbox[2])
        y2 = min(bottom, y1 + bbox[3])
        x1 = max(left, x1)
        y1 = max(top, y1)
        if x1 >= (x2 - min_box_width) or y1 >= (y2 - min_box_height):
            continue
        labels.append(label)
        bboxes.append(
            (
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                x2 - x1,
                y2 - y1,
            )
        )
    return {
        "bboxes": bboxes,
        "labels": labels,
        "canvas_size": (right - left, bottom - top),
    }
