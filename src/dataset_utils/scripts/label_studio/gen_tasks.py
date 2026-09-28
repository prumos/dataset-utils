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
            "--classes",
            type=str,
            nargs="*",
            default=None,
            help="Targeted classes for generating the tasks.",
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
            target_classes=args.classes,
            json_indentation=args.indent,
            prepare_target_storage=True,
        )
        return 0
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(_run())
