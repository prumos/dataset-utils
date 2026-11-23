import argparse
from pathlib import Path

import torch
from ultralytics import YOLO

from dataset_utils.training import total_uncertainty_selection
from dataset_utils.detection_utils import list_images_in_directory


def _main(
    model_weights: Path,
    images_dir: Path,
    destination_dir: Path,
    selection_size: int,
) -> None:
    model = YOLO(model_weights)
    selection = total_uncertainty_selection(
        model=model,
        imgs=list_images_in_directory(images_dir),
        selection_size=selection_size,
    )
    destination_dir.mkdir(parents=True, exist_ok=True)
    for selected_index in selection["selection"]:
        image = selection["images"][selected_index]
        result = model.predict(
            source=image,
            stream=False,
            imgsz=model.overrides["imgsz"],
            conf=0.25,
            iou=0.7,  # In case the model do not have NMS-free heads
            nms=False,
            device=(0 if torch.cuda.is_available() else "cpu"),
            verbose=False,
        )
        result[0].save_txt(destination_dir / f"{image.stem}.txt")
        image.rename(destination_dir / image.name)


def _get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--imgs",
        type=Path,
        help="Directory path from where to select images.",
    )
    parser.add_argument(
        "-d",
        "--dest",
        type=Path,
        help="Destination where to move the selected images.",
    )
    parser.add_argument(
        "-m",
        "--model",
        type=Path,
        help="Selection model's weights.",
    )
    parser.add_argument(
        "-s",
        "--size",
        type=int,
        help="Number of images to select.",
    )
    return parser


def _run() -> int:
    try:
        parser = _get_args_parser()
        args = parser.parse_args()
        _main(
            model_weights=args.model,
            images_dir=args.imgs,
            destination_dir=args.dest,
            selection_size=args.size,
        )
        return 0
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(_run())
