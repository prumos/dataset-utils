from pathlib import Path
from typing import TypedDict, NotRequired


class YOLODetection(TypedDict):
    bboxes: tuple[float, float, float, float]
    indexes: list[int]
    labels: NotRequired[list[str]]


def load_index_name_map(classes_file: str | Path) -> dict[int, str]:
    index_name_map = {
        i: class_name.strip()
        for i, class_name in enumerate(
            Path(classes_file).read_text().strip().splitlines()
        )
    }
    return index_name_map


def load_detection_annotation(
    annotation_file: str | Path,
    index_name_map: dict[int, str] | None = None,
) -> YOLODetection:
    indexes = []
    bboxes = []
    for line in Path(annotation_file).read_text().strip().splitlines():
        label, *coords = line.strip().split()
        # YOLO format is: class id, x center, y center, width, height
        # Coordinates and dimensions are normalized by image width and height
        x, y, w, h = (float(coord) for coord in coords)
        indexes.append(int(label))
        bboxes.append(
            (
                max(0.0, min(1.0, x)),
                max(0.0, min(1.0, y)),
                max(0.0, min(1.0, w)),
                max(0.0, min(1.0, h)),
            )
        )
    detection = {"indexes": indexes, "bboxes": bboxes}
    if index_name_map is not None:
        detection["labels"] = [index_name_map[idx] for idx in indexes]
    return detection


def write_detection_to_annotation(
    detection: YOLODetection,
    annotation_file: str | Path,
):
    lines = [
        "{:d} {:8f} {:8f} {:8f} {:8f}\n".format(idx, *coords)
        for idx, coords in zip(detection["indexes"], detection["bboxes"])
    ]
    with open(annotation_file, "w") as ann_file:
        ann_file.writelines(lines)
