import argparse
import yaml
import shutil
from collections import defaultdict
from collections.abc import Hashable
from pathlib import Path

from dataset_utils import label_studio, yolo, training


def _get_image_group(image_path: Path) -> Hashable:
    return image_path.parts[-2]


def prepare_yolo_dataset(
    tasks: list[label_studio.LabelStudioTask],
    train_ratio: float,
    valid_ratio: float,
    test_ratio: float,
    save_dir: Path,
):
    image_detection_map = {}
    local_files_prefix = "/data/local-files/?d=images/"
    local_imgs_dir = None
    classes = set()
    for task in tasks:
        data_image: str = task["data"]["image"]
        if data_image.startswith(local_files_prefix):
            data_image = data_image.removeprefix(local_files_prefix)
            try:
                image_path = local_imgs_dir / data_image
            except TypeError:
                local_imgs_dir = label_studio.get_local_files_root() / "images"
                image_path = local_imgs_dir / data_image
        else:
            image_path = Path(data_image)
        try:
            detection = label_studio.yolo_detections_from_task(task)[0]
        except TypeError:
            continue
        classes.update(detection["labels"])
        image_detection_map[image_path] = detection
    classes = sorted(classes)
    image_groups = defaultdict(list)
    for image_path in image_detection_map:
        image_groups[_get_image_group(image_path)].append(image_path)
    train_split = []
    valid_split = []
    test_split = []
    for group_images in image_groups.values():
        group_images.sort()
        splits = training.sequential_split(
            group_images, [train_ratio, valid_ratio, test_ratio]
        )
        train_split.extend(splits[0])
        valid_split.extend(splits[1])
        test_split.extend(splits[2])
    save_dir = save_dir.resolve()
    save_dir.mkdir(parents=True, exist_ok=True)
    images_dir = save_dir / "images"
    images_dir.mkdir(exist_ok=True)
    labels_dir = save_dir / "labels"
    labels_dir.mkdir(exist_ok=True)
    # Save dataset locally
    dataset_metadata = {"path": save_dir.as_posix()}
    class_index_map = {cls_name: i for i, cls_name in enumerate(classes)}
    for split, split_images in zip(
        ("train", "valid", "test"),
        (train_split, valid_split, test_split),
    ):
        images_split_dir = images_dir / split
        images_split_dir.mkdir(exist_ok=True)
        labels_split_dir = labels_dir / split
        labels_split_dir.mkdir(exist_ok=True)
        if split_images:
            dataset_metadata[split if split != "valid" else "val"] = (
                images_split_dir.relative_to(save_dir).as_posix()
            )
        for image_path in split_images:
            detection = image_detection_map[image_path]
            detection["labels"] = [
                class_index_map[label] for label in detection["labels"]
            ]
            shutil.copy2(image_path, images_split_dir / image_path.name)
            yolo.write_detection_to_annotation(
                detection=detection,
                ann_path=labels_split_dir / f"{image_path.stem}.txt",
            )
    # Save dataset metadate as YAML
    dataset_metadata["names"] = {
        i: class_name for i, class_name in enumerate(classes)
    }
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
        "-n",
        "--name",
        type=str,
        required=True,
        help="The name of the dataset."
    )
    parser.add_argument(
        "-s",
        "--save_dir",
        type=Path,
        required=True,
        help="Where to save the dataset.",
    )
    parser.add_argument(
        "-p",
        "--projects_dir",
        type=Path,
        default="label_studio/projects/json",
        help="Where the projects are stored.",
    )
    parser.add_argument(
        "-gp",
        "--glob_pattern",
        type=str,
        default="*.json",
        help=(
            "Glob pattern for matching project "
            "names in stored in '--projects_dir'"
        )
    )
    parser.add_argument(
        "-tr",
        "--train_ratio",
        type=float,
        default=0.7,
        help="Ratio of the train split/set.",
    )
    parser.add_argument(
        "-vr",
        "--valid_ratio",
        type=float,
        default=0.15,
        help="Ratio of the valid split/set.",
    )
    return parser


def _run():
    try:
        parser = _get_args_parser()
        args = parser.parse_args()
        tasks = []
        for project in args.projects_dir.glob(args.glob_pattern):
            tasks.extend(label_studio.load_json_project(project))
        prepare_yolo_dataset(
            tasks=tasks,
            train_ratio=args.train_ratio,
            valid_ratio=args.valid_ratio,
            test_ratio=(1.0 - args.train_ratio - args.valid_ratio),
            save_dir=(args.save_dir / args.name),
        )
        return 0
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(_run())
