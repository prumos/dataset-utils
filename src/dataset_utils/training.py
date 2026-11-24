import math
from collections.abc import Sequence
from typing import TypedDict, TypeVar
from pathlib import Path

import torch
from ultralytics import YOLO
from ultralytics.engine.results import Results


def check_ratios(ratios: list[float]) -> list[float]:
    total_sum = sum(ratios)
    if not math.isclose(total_sum, 1.0, rel_tol=0, abs_tol=1e-9):
        raise ValueError(f"Rations do not sum to 1.0, got {total_sum}")
    for i, ratio in enumerate(ratios):
        if ratio < 0.0 or ratio > 1.0:
            raise ValueError(
                f"Ration at index {i} is not in [0, 1], got {ratio}"
            )
    return ratios


def sequential_split[T](
    items: Sequence[T],
    ratios: Sequence[float],
) -> list[list[T]]:
    check_ratios(ratios)
    total_items = len(items)
    exact_counts = [total_items * ratio for ratio in ratios]
    splits_num_items = [math.floor(count) for count in exact_counts]
    remaining = total_items - sum(splits_num_items)
    remainder_order = sorted(
        range(len(ratios)),
        key=(lambda x: exact_counts[x] - splits_num_items[x]),
        reverse=True,
    )
    for i in remainder_order[:remaining]:
        splits_num_items[i] += 1
    splits: list[list[T]] = []
    start = 0
    for count in splits_num_items:
        end = start + count
        splits.append(list(items[start:end]))
        start = end
    return splits


class ImagesSelection[T: (str, Path)](TypedDict):
    images: Sequence[T]
    scores: list[float]
    selection: list[int]


def total_uncertainty_selection[T: (str, Path)](
    model: YOLO,
    imgs: Sequence[T],
    selection_size: int,
    target_classes: list[str] | None = None,
) -> ImagesSelection[T]:
    scores: list[float] = []
    targets = frozenset(
        (i for i, name in model.names.items() if name in target_classes)
        if target_classes
        else model.names
    )
    for img in imgs:
        result = model.predict(
            source=img,
            stream=False,
            imgsz=model.overrides["imgsz"],
            conf=1e-4,
            iou=1.0,  # In case the model do not have NMS-free heads
            nms=False,
            device=(0 if torch.cuda.is_available() else "cpu"),
            verbose=False,
        )[0]
        scores.append(
            sum(
                1.0 - float(conf.item())
                for cls, conf in zip(result.boxes.cls, result.boxes.conf)
                if cls in targets
            )
        )
    ordering = sorted(
        range(len(imgs)),
        key=(lambda i: scores[i]),
        reverse=True,
    )
    return {
        "images": imgs,
        "scores": scores,
        "selection": ordering[:selection_size],
    }
