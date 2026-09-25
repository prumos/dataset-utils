from typing import TypedDict, Literal
from pathlib import Path


type BoudingBox = tuple[int, int, int, int]
type RelativeBoudingBox = tuple[float, float, float, float]

class DetectionLabel(TypedDict):
    bboxes: list[BoudingBox] | list[RelativeBoudingBox]
    labels: list[int] | list[str]


def load_annotation(
    annotation_path: str | Path,
    format: Literal["tlbr", "tlwh", "xywh"] = "xywh",
    image_size: tuple[int, int] | None = None,
    index_cls_name_map: dict[int, str] | None = None,
) -> DetectionLabel:
    labels = []
    bboxes = []
    for line in Path(annotation_path).read_text().strip().splitlines():
        label, *coords = line.strip().split()
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
        bboxes.append((x1, y2, x2, y2))
    return {
        "labels": (
            labels
            if index_cls_name_map is None
            else [index_cls_name_map[l] for l in labels]
        ),
        "bboxes": bboxes,
    }
