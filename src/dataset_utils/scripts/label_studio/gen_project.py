import argparse
import json

from dataset_utils.label_studio import gen_tasks_for_local_images


def _run() -> int:
    try:
        parser = argparse.ArgumentParser(
            description=(
                "Generate a Label Studio project (list of tasks) from the "
                "configured local storage. Local files serving must be "
                "enabled and configured."
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
            "-s",
            "--save_file",
            type=str,
            required=True,
            help="Path to save the generated project as a JSON file.",
        )
        parser.add_argument(
            "--img_fmts",
            type=str,
            nargs="+",
            default=[".jpg", ".png"],
            help="Image formats to consider.",
        )
        parser.add_argument(
            "--indentation",
            type=int,
            default=2,
            help="Set JSON indentation size."
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Print the generated project in stdout.",
        )
        args = parser.parse_args()
        project = gen_tasks_for_local_images(
            images_dir=args.images_dir,
            image_formats=args.img_fmts,
            json_save_file=args.save_file,
            json_indentation=args.indentation,
        )
        indent = None if args.indentation < 1 else args.indentation
        with open(args.save_file, mode="w") as json_file:
            json_string = json.dumps(obj=project, indent=indent)
            json_file.write(json_string)
            if args.verbose:
                print(json_string)
        return 0
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(_run())
