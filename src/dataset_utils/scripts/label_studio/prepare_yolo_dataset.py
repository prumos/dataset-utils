import argparse
from collections import defaultdict
import yaml
import shutil
from pathlib import Path

from PIL import Image

from dataset_utils import detection_utils, label_studio, training, yolo


def _preprare_destination(save_dir: Path) -> Path:
    save_dir = Path(save_dir).resolve()
    save_dir.mkdir(parents=True, exist_ok=True)
    images_dir = save_dir / "images"
    images_dir.mkdir(exist_ok=True)
    labels_dir = save_dir / "labels"
    labels_dir.mkdir(exist_ok=True)
    return save_dir


def prepare_yolo_dataset(config_file: str | Path):
    with open(config_file, mode="r") as config_file:
        config = yaml.safe_load(config_file)
    projects_dir = Path(config["projects_dir"]).resolve()
    local_imgs_dir = label_studio.get_local_files_root()
    save_dir = _preprare_destination(config["save_dir"])
    classes = set()
    dataset_metadata = {"path": save_dir.as_posix()}
    detections_store = defaultdict(dict)
    for project_config in config["projects"].values():
        image_detec_map = {}
        for task in label_studio.load_json_project(
            projects_dir / project_config["filename"]
        ):
            image_path = local_imgs_dir / task["data"]["image"].removeprefix(
                label_studio.LOCAL_FILES_PREFIX
            )
            detection = label_studio.detections_from_task(task)
            if detection is None:
                continue
            detection = detection[0]
            if detection["canvas_size"][0] == 1:
                with Image.open(image_path) as img:
                    detection = detection_utils.scale_detection(
                        detection=detection,
                        canvas_size=img.size,
                    )
            classes.update(detection["labels"])
            image_detec_map[image_path] = detection
        splits = sorted(project_config.get("splits", []))
        if not splits:
            splits = ["train"]
            image_splits = [sorted(image_detec_map)]
        else:
            image_splits = training.sequential_split(
                items=sorted(image_detec_map),
                ratios=training.check_ratios(
                    [project_config["splits"][split] for split in splits]
                ),
            )
        rois = project_config.get("rois", {})
        for split, images in zip(splits, image_splits):
            if not images:
                continue
            images_split_dir = save_dir / "images" / split
            images_split_dir.mkdir(exist_ok=True)
            dataset_metadata[split] = (
                images_split_dir.relative_to(save_dir).as_posix()
            )
            for image_path in images:
                if rois:
                    detection = image_detec_map[image_path]
                    with Image.open(image_path) as img:
                        for name, coords in rois.items():
                            roi_img = img.crop(coords)
                            roi_detec = detection_utils.crop_detection(
                                detection, *coords,
                            )
                            dest_path = images_split_dir / (
                                f"{image_path.stem}_{name}{image_path.suffix}"
                            )
                            detections_store[split][dest_path.stem] = roi_detec
                            roi_img.save(dest_path)
                else:
                    detection = image_detec_map[image_path]
                    detections_store[split][image_path.stem] = detection
                    shutil.copy2(image_path, images_split_dir / image_path.name)
    classes = sorted(classes)
    dataset_metadata["names"] = {
        i: cls_name for i, cls_name in enumerate(classes)
    }
    name_index_map = {cls_name: i for i, cls_name in enumerate(classes)}
    for split, stem_detect_map in detections_store.items():
        labels_split_dir = save_dir / "labels" / split
        labels_split_dir.mkdir(exist_ok=True)
        for ann_stem, detection in stem_detect_map.items():
            detection = detection_utils.scale_detection(
                detection=detection,
                canvas_size=(1, 1),
            )
            detection["indexes"] = [
                name_index_map[label] for label in detection["labels"]
            ]
            yolo.write_detection_to_annotation(
                detection=detection,
                annotation_file=(labels_split_dir / f"{ann_stem}.txt"),
            )
    with (save_dir / f"{save_dir.name}.yaml").open("w") as metadata_yaml:
        yaml.dump(
            data=dataset_metadata,
            stream=metadata_yaml,
            indent=2,
            sort_keys=False,
        )
    return


def _get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare a YOLO custom dataset from a list "
            "of Label Studio exported JSON projects."
        )
    )
    parser.add_argument(
        "config_file",
        type=Path,
        help="Configuration file that stipulates how to generate the dataset.",
    )
    return parser


def _run():
    try:
        parser = _get_args_parser()
        args = parser.parse_args()
        prepare_yolo_dataset(args.config_file)
        return 0
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(_run())
