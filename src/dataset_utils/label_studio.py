import os
import json
from pathlib import Path
from typing import NotRequired, TypedDict, Any

from dataset_utils.yolo import load_annotation, load_index_class_map


type LabelStudioPrediction = dict[str, Any]
type LabelStudioAnnotation = dict[str, Any]

class LabelStudioTask(TypedDict):
    data: dict[str, Any]
    annotations: NotRequired[list[LabelStudioAnnotation]]
    predictions: NotRequired[list[LabelStudioPrediction]]


def prediction_from_yolo_annotation(
    annotation_path: str,
    index_cls_name_map: dict[int, str],
    include_classes: list[str] | None = None,
    exclude_classes: list[str] | None = None,
    from_name_value: str = "label",
    to_name_value: str = "image",
    type_value: str = "rectanglelabels",
    source_value: str = "$image",
    model_version: str  = "",
) -> LabelStudioPrediction:
    annotation = load_annotation(
        annotation_path,
        format="tlwh",
        index_cls_name_map=index_cls_name_map,
    )
    target_classes = frozenset(annotation["labels"])
    if include_classes is not None:
        target_classes = target_classes.intersection(include_classes)
    if exclude_classes is not None:
        target_classes = target_classes.difference(exclude_classes)
    return {
        "model_version": model_version,
        "result": [
            {
                "from_name": from_name_value,
                "to_name": to_name_value,
                "type": type_value,
                "source": source_value,
                "value": {
                    "rectanglelabels": [label],
                    "x": bbox[0] * 100.0,
                    "y": bbox[1] * 100.0,
                    "width": bbox[2] * 100.0,
                    "height": bbox[3] * 100.0,
                }
            }
            for label, bbox in zip(annotation["labels"], annotation["bboxes"])
            if label in target_classes
        ]
    }


def _get_task_for_local_image(rel_img_path: str) -> LabelStudioTask:
    return {
        "data": {
            "image": f"/data/local-files/?d={rel_img_path}",
        }
    }


def get_local_files_root(fallback: str | Path = "/") -> Path:
    enabled = os.environ.get("LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED", "")
    if enabled != "true":
        raise RuntimeError(
            "Local file serving is not enabled. "
            'Set "LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED" to "true" and '
            '"LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT" to the appropriate path.'
        )
    local_files_root  = os.environ.get(
        "LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT",
        "",
    )
    local_files_root = local_files_root if local_files_root else fallback
    return Path(local_files_root).resolve()


def check_file_formats(fmts: list[str]) -> list[str]:
    return sorted(
        frozenset((fmt if fmt.startswith(".") else f".{fmt}") for fmt in fmts)
    )


def gen_tasks_for_local_images(
    images_dir: str | Path,
    image_fmts: list[str] = [".jpg", ".png"],
    recurse_dir: bool = False,
    include_classes: list[str] | None = None,
    exclude_classes: list[str] | None = None,
    json_indentation: int | None = 2,
    prepare_target_storage: bool = False,
) -> None:
    local_root = get_local_files_root()
    images_dir = Path(images_dir).resolve()
    if not images_dir.is_relative_to(local_root):
        raise ValueError(
            f'"{images_dir}" is not part of the '
            'local files root tree "{local_root}"'
        )
    image_fmts = frozenset(check_file_formats(image_fmts))
    target_dirs = (
        [Path(step[0]) for step in os.walk(images_dir)]
        if recurse_dir
        else [images_dir]
    )
    for images_dir in target_dirs:
        classes_file = images_dir / "classes.txt"
        index_cls_map = (
            load_index_class_map(classes_file)
            if classes_file.is_file()
            else None
        )
        for img in (
            item for item in images_dir.iterdir() if item.suffix in image_fmts
        ):
            task = _get_task_for_local_image(
                img.relative_to(local_root).as_posix()
            )
            if index_cls_map is not None:
                try:
                    task["predictions"] = [
                        prediction_from_yolo_annotation(
                            annotation_path=img.with_suffix(".txt"),
                            index_cls_name_map=index_cls_map,
                            include_classes=include_classes,
                            exclude_classes=exclude_classes,
                        )
                    ]
                except FileNotFoundError:
                    pass
            with img.with_suffix(".json").open("w") as task_file:
                json.dump(obj=task, fp=task_file, indent=json_indentation)
        if prepare_target_storage:
            target_storage = Path(
                images_dir.as_posix().replace("/images/", "/annotations/", 1)
            )
            target_storage.mkdir(parents=True, exist_ok=True)
    return
