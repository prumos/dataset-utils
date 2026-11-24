import argparse

from dataset_utils.label_studio import gen_tasks_for_local_images


def _main(
    image_dirs: list[str],
    image_extensions: list[str] | None = None,
    include_classes: list[str] | None = None,
    exclude_classes: list[str] | None = None,
    json_indent: int | None = None,
) -> None:
    for imgs_dir in image_dirs:
        gen_tasks_for_local_images(
            images_dir=imgs_dir,
            image_extensions=image_extensions,
            include_classes=include_classes,
            exclude_classes=exclude_classes,
            json_indent=json_indent,
        )


def _get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Label Studio tasks for images in the local storage. "
            "Local files serving must be enabled and configured. "
            "Tasks are created in the local storage alongside the images."
        )
    )
    parser.add_argument(
        "imgs",
        type=str,
        nargs="+",
        help=(
            "Targeted directories. The directories must be inside the "
            "Label Studio local files root configured during startup."
        ),
    )
    parser.add_argument(
        "--extensions",
        type=str,
        nargs="+",
        default=None,
        help="Image extensions (e.g.: .jpg, .png, ...) to consider.",
    )
    parser.add_argument(
        "--include",
        type=str,
        nargs="*",
        default=None,
        help=(
            "Classes to INCLUDE in the tasks if YOLO predictions are available."
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
        help="Set JSON indentation size.",
    )
    return parser


def _run() -> int:
    try:
        parser = _get_args_parser()
        args = parser.parse_args()
        _main(
            image_dirs=args.imgs,
            image_extensions=args.extensions,
            include_classes=args.include,
            exclude_classes=args.exclude,
            json_indent=args.indent,
        )
        return 0
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(_run())
