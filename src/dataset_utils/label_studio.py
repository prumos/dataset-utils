import os
import json
from pathlib import Path

from dataset_utils.yolo import load_annotation
from dataset_utils.yolo import index_class_name_map_from_class_file


def prediction_from_yolo_annotation(
    annotation_path: str,
    index_cls_name_map: dict[int, str],
    from_name_value: str = "label",
    to_name_value: str = "image",
    type_value: str = "rectanglelabels",
    source_value: str = "$image",
    model_version: str | None = None,
):
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
                    "rectanglelabels": label,
                    "x": bbox[0] * 100.0,
                    "y": bbox[1] * 100.0,
                    "width": bbox[2] * 100.0,
                    "height": bbox[3] * 100.0,
                }
            }
            for label, bbox in zip(annotation["labels"], annotation["bboxes"])
        ]
    }


def _gen_task_for_local_image(rel_img_path: str):
    return {
        "data": {
            "image": f"/data/local-files/?d={rel_img_path}",
        }
    }


def get_local_files_root(fallback: str | Path = "/") -> Path | None:
    enabled = os.environ.get("LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED", "")
    if enabled != "true":
        return None
    local_files_root  = os.environ.get(
        "LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT",
        "",
    )
    local_files_root = local_files_root if local_files_root else fallback
    return Path(local_files_root).resolve()


def gen_tasks_for_local_images(
    images_rel_path: str,
    image_formats: list[str] = [".jpg", ".png"],
    json_save_file: str | Path | None = None,
    json_indentation: int = 2,
):
    local_root = get_local_files_root()
    if local_root is None:
        raise RuntimeError(
            "Local file serving is not enabled. "
            'Set "LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED" to "true" and '
            '"LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT" to the appropriate path.'
        )
    images_dir = (local_root / images_rel_path).absolute()
    images = []
    for fmt in image_formats:
        images.extend(images_dir.glob(f"*{fmt}"))
    classes_file = images_dir / "classes.txt"
    index_cls_map = (
        index_class_name_map_from_class_file(classes_file)
        if classes_file.is_file()
        else None
    )
    tasks = []
    for img in images:
        task = _gen_task_for_local_image(img.relative_to(local_root))
        if index_cls_map is not None:
            task["predictions"] = [
                prediction_from_yolo_annotation(
                    annotation_path=img.with_suffix(".txt"),
                    index_cls_name_map=index_cls_map,
                )
            ]
    if json_save_file is not None:
        json_indentation = None if json_indentation < 1 else json_indentation
        with Path(json_save_file).open("w") as json_save_file:
            json.dump(obj=tasks, fp=json_save_file, indent=json_indentation)
    return tasks
