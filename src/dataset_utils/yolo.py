from pathlib import Path

from dataset_utils.detection_utils import DetectionBoudingBoxes


def load_index_name_map(classes_file: str | Path) -> dict[int, str]:
    index_name_map = {
        i: class_name.strip()
        for i, class_name in enumerate(
            Path(classes_file).read_text().strip().splitlines()
        )
    }
    return index_name_map


def load_detection_from_annotation(
    annotation_file: str | Path,
    canvas_size: tuple[int, int] = (1, 1),
    index_name_map: dict[int, str] | None = None,
) -> DetectionBoudingBoxes:
    indexes = []
    bboxes = []
    width, height = canvas_size
    for line in Path(annotation_file).read_text().strip().splitlines():
        label, *coords = line.strip().split()
        # YOLO format is: class id, x center, y center, width, height
        # Coordinates and dimensions are normalized by image width and height
        x, y, w, h = (float(coord) for coord in coords)
        indexes.append(int(label))
        bboxes.append(
            (
                width * max(0.0, min(1.0, x)),
                height * max(0.0, min(1.0, y)),
                width * max(0.0, min(1.0, w)),
                height * max(0.0, min(1.0, h)),
            )
        )
    detection = {
        "bboxes": bboxes,
        "canvas_size": canvas_size,
        "indexes": indexes,
    }
    if index_name_map is not None:
        detection["labels"] = [index_name_map[idx] for idx in indexes]
    return detection


def write_detection_to_annotation(
    detection: DetectionBoudingBoxes,
    annotation_file: str | Path,
):
    lines = [
        "{:d} {:8f} {:8f} {:8f} {:8f}\n".format(idx, *coords)
        for idx, coords in zip(detection["indexes"], detection["bboxes"])
    ]
    with open(annotation_file, "w") as ann_file:
        ann_file.writelines(lines)
