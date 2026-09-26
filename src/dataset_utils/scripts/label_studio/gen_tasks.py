import argparse
import json
from pathlib import Path

from dataset_utils.label_studio import gen_tasks_for_local_images


def _run() -> int:
    try:
        parser = argparse.ArgumentParser(
            description=(
                "Generate Label Studio tasks for images in the local storage. "
                "Local files serving must be enabled and configured. "
                "Tasks are created in the local storage alongside the images."
            )
        )
        parser.add_argument(
            "-d",
            "--images_dir",
            type=str,
            required=True,
            help=(
                "Path to the directory containing the target images. "
                "The directory must be inside the Label Studio local files "
                "document root configured during Label Studio startup."
            ),
        )
        parser.add_argument(
            "--images_fmts",
            type=str,
            nargs="+",
            default=[".jpg", ".png"],
            help="Image formats to consider.",
        )
        parser.add_argument(
            "-dr",
            "--disable_recurse",
            action="store_true",
            help="Disable directory recursive search for images."
        )
        parser.add_argument(
            "--indentation",
            type=int,
            default=2,
            help="Set JSON indentation size."
        )
        args = parser.parse_args()
        indent = None if args.indentation < 1 else args.indentation
        gen_tasks_for_local_images(
            images_dir=args.images_dir,
            image_formats=args.images_fmts,
            json_indentation=indent,
            recurse_images_dir=(not args.disable_recurse),
        )
        return 0
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(_run())
