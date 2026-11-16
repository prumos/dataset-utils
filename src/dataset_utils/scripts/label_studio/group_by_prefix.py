import argparse
from collections import defaultdict
import json
from pathlib import Path

from dataset_utils import label_studio


def _main(
    project_files: list[Path],
    save_dir: Path,
    indent: int | None = None,
) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    tasks_by_prefix: dict[str, list[label_studio.LabelStudioTask]] = (
        defaultdict(list)
    )
    for project in project_files:
        for task in label_studio.load_json_project(project):
            image: str = task["data"]["image"]
            image = image.removeprefix(label_studio.LOCAL_FILES_PREFIX)
            prefix = Path(image).stem.split("_", maxsplit=1)[0]
            tasks_by_prefix[prefix].append(task)
    for prefix, tasks in tasks_by_prefix.items():
        prefix_project = save_dir / f"{prefix}.json"
        tasks.sort(key=(lambda x: x["data"]["image"]))
        with prefix_project.open("w") as proj_file:
            json.dump(obj=tasks, fp=proj_file, indent=indent)


def _get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Split the tasks in a project based "
            "on the prefix of the image names."
        )
    )
    parser.add_argument(
        "projects",
        type=Path,
        help="Path to a JSON project or to a directory with projects.",
    )
    parser.add_argument(
        "save_dir",
        type=Path,
        help="Path to a directory where to save the splits.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=None,
        help="Indentation size for saving JSON files.",
    )
    return parser


def _run():
    try:
        parser = _get_args_parser()
        args = parser.parse_args()
        projects: Path = args.projects
        if projects.is_file():
            projects = [projects]
        else:
            projects = list(projects.glob("*.json"))
        _main(
            project_files=projects,
            save_dir=args.save_dir,
            indent=args.indent,
        )
        return 0
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(_run())
