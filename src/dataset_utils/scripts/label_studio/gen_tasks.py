import argparse

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
            "--fmts",
            type=str,
            nargs="+",
            default=[".jpg", ".png"],
            help="Image formats to consider.",
        )
        parser.add_argument(
            "--recurse",
            action="store_true",
            help="Recurse subdirectories in the file tree.",
        )
        parser.add_argument(
            "--include",
            type=str,
            nargs="*",
            default=None,
            help=(
                "Classes to INCLUDE in the tasks "
                "if YOLO predictions are available."
            ),
        )
        parser.add_argument(
            "--exclude",
            type=str,
            nargs="*",
            default=None,
            help=(
                "Classes to EXCLUDE from the tasks "
                "if YOLO predictions are available."
            ),
        )
        parser.add_argument(
            "--indent",
            type=int,
            default=None,
            help="Set JSON indentation size."
        )
        args = parser.parse_args()
        gen_tasks_for_local_images(
            images_dir=args.images_dir,
            image_fmts=args.fmts,
            recurse_dir=args.recurse,
            include_classes=args.include,
            exclude_classes=args.exclude,
            json_indentation=args.indent,
        )
        return 0
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(_run())
