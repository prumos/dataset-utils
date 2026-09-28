from pathlib import Path
from typing import TypedDict, Literal


type AbsoluteBoudingBox = tuple[int, int, int, int]
type RelativeBoudingBox = tuple[float, float, float, float]

class DetectionAnnotation(TypedDict):
    bboxes: list[AbsoluteBoudingBox] | list[RelativeBoudingBox]
    labels: list[int] | list[str]


def load_index_class_map(classes_file: str | Path) -> dict[int, str]:
    index_class_map = {
        i: class_name.strip()
        for i, class_name in enumerate(
            Path(classes_file).read_text().strip().splitlines()
        )
    }
    return index_class_map


def load_annotation(
    annotation_path: str | Path,
    format: Literal["tlbr", "tlwh", "xywh"] = "xywh",
    image_size: tuple[int, int] | None = None,
    index_cls_name_map: dict[int, str] | None = None,
) -> DetectionAnnotation:
    labels = []
    bboxes = []
    for line in Path(annotation_path).read_text().strip().splitlines():
        label, *coords = line.strip().split()
        # YOLO format is: class id, x center, y center, width, height
        # Coordinates and dimensions are normalized by image width and height
        x1, y1, x2, y2 = (float(coord) for coord in coords)
        if format == "tlwh":
            x1, y1 = (x1 - x2 / 2), (y1 - y2 / 2)
        if format == "tlbr":
            x1, y1 = (x1 - x2 / 2), (y1 - y2 / 2)
            x2, y2 = (x1 + x2), (y1 + y2)
        if image_size is not None:
            w, h = image_size
            x1, x2 = round(x1 * w), round(x2 * w)
            y1, y2 = round(y1 * h), round(y2 * h)
        labels.append(int(label))
        bboxes.append((x1, y1, x2, y2))
    if index_cls_name_map is None:
        return {"labels": labels, "bboxes": bboxes}
    filtered_labels = []
    filtered_bboxes = []
    for label, bbox in zip(labels, bboxes):
        try:
            filtered_labels.append(index_cls_name_map[label])
            filtered_bboxes.append(bbox)
        except KeyError:
            continue
    return {"labels": filtered_labels, "bboxes": filtered_bboxes}
