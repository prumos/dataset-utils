import math
from typing import TypeVar, Protocol
from collections.abc import Sequence

T = TypeVar("T")

class Splitter(Protocol[T]):
    def __call__(
        self,
        items: Sequence[T],
        ratios: Sequence[float],
    ) -> list[list[T]]:
        ...


def check_ratios(ratios: list[float]):
    total_sum = sum(ratios)
    if not math.isclose(total_sum, 1.0, rel_tol=0, abs_tol=1e-9):
        raise ValueError(f"Rations do not sum to 1.0, got {total_sum}")
    for i, ratio in enumerate(ratios):
        if ratio < 0.0 or ratio > 1.0:
            raise ValueError(f"Ration at index {i} is not in [0, 1], got {ratio}")


def sequential_split(
    items: Sequence[str],
    ratios: Sequence[float],
) -> list[list[str]]:
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
    splits = []
    start = 0
    for count in splits_num_items:
        end = start + count
        splits.append(list(items[start:end]))
        start = end
    return splits
