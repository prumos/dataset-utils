import os
import json
from collections import defaultdict
from collections.abc import Callable, Hashable
from math import ceil
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
    from_name_value: str = "label",
    to_name_value: str = "image",
    type_value: str = "rectanglelabels",
    source_value: str = "$image",
    model_version: str | None = None,
) -> LabelStudioPrediction:
    annotation = load_annotation(
        annotation_path,
        format="tlwh",
        index_cls_name_map=index_cls_name_map,
    )
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


def _check_file_formats(fmts: list[str]) -> list[str]:
    return sorted(
        frozenset((fmt if fmt.startswith(".") else f".{fmt}") for fmt in fmts)
    )


def get_tasks_for_local_images(
    images_dir: str | Path,
    image_formats: list[str] = [".jpg", ".png"],
    recurse_images_dir: bool = True,
) -> list[LabelStudioTask]:
    local_root = get_local_files_root()
    images_dir = Path(images_dir).resolve()
    if not images_dir.is_relative_to(local_root):
        raise ValueError(
            f'"{images_dir}" is not part of the '
            'local files root tree "{local_root}"'
        )
    image_formats = _check_file_formats(image_formats)
    classes_file = images_dir / "classes.txt"
    index_cls_map = (
        load_index_class_map(classes_file)
        if classes_file.is_file()
        else None
    )
    tasks = []
    for fmt in image_formats:
        for img in (
            images_dir.rglob(f"*{fmt}")
            if recurse_images_dir
            else images_dir.glob(f"*{fmt}")
        ):
            task = _get_task_for_local_image(img.relative_to(local_root).as_posix())
            if index_cls_map is not None:
                try:
                    task["predictions"] = [
                        prediction_from_yolo_annotation(
                            annotation_path=img.with_suffix(".txt"),
                            index_cls_name_map=index_cls_map,
                        )
                    ]
                except FileNotFoundError:
                    pass
            tasks.append(task)
    return tasks


def gen_tasks_for_local_images(
    images_dir: str | Path,
    image_formats: list[str] = [".jpg", ".png"],
    json_indentation: int = 2,
    recurse_images_dir: bool = True,
) -> None:
    local_root = get_local_files_root()
    images_dir = Path(images_dir).resolve()
    if not images_dir.is_relative_to(local_root):
        raise ValueError(
            f'"{images_dir}" is not part of the '
            'local files root tree "{local_root}"'
        )
    image_formats = _check_file_formats(image_formats)
    json_indentation = None if json_indentation < 1 else json_indentation
    classes_file = images_dir / "classes.txt"
    index_cls_map = (
        load_index_class_map(classes_file)
        if classes_file.is_file()
        else None
    )
    for fmt in image_formats:
        for img in (
            images_dir.rglob(f"*{fmt}")
            if recurse_images_dir
            else images_dir.glob(f"*{fmt}")
        ):
            task = _get_task_for_local_image(img.relative_to(local_root).as_posix())
            if index_cls_map is not None:
                try:
                    task["predictions"] = [
                        prediction_from_yolo_annotation(
                            annotation_path=img.with_suffix(".txt"),
                            index_cls_name_map=index_cls_map,
                        )
                    ]
                except FileNotFoundError:
                    pass
            with img.with_suffix(".json").open("w") as task_file:
                json.dump(obj=task, fp=task_file, indent=json_indentation)
    return


def split_tasks(
    tasks: list[LabelStudioTask],
    num_splits_or_splitter: int | Callable[[LabelStudioTask], Hashable],
) -> list[list[LabelStudioTask]]:
    if isinstance(num_splits_or_splitter, int):
        num_splits = num_splits_or_splitter
        tasks_per_split = ceil(len(tasks) / num_splits)
        return [
            tasks[i * tasks_per_split : (i + 1) * tasks_per_split]
            for i in range(num_splits)
        ]
    splitter = num_splits_or_splitter
    groups = defaultdict(list)
    for task in tasks:
        groups[splitter(task)].append(task)
    return list(groups.values())
