from __future__ import annotations

import csv
import os
import random
import sys


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from differentiator import differentiate
from generator import generate
from simplify import simplify


GROUPS = {
    "simple": {"max_depth": 2, "nodes_range": (2, 8), "count": 250},
    "medium": {"max_depth": 3, "nodes_range": (9, 15), "count": 250},
    "hard": {"max_depth": 4, "nodes_range": (16, 20), "count": 250},
}


def build_group_csv(name: str, max_depth: int, nodes_min: int, nodes_max: int, count: int) -> str:
    rows: list[tuple[str, str]] = []

    for _ in range(count):
        nodes = random.randint(nodes_min, nodes_max)
        expr = generate(max_depth=max_depth, nodes=nodes)
        derivative = simplify(differentiate(expr))
        rows.append((derivative.pretty(), expr.pretty()))

    out_path = os.path.join(ROOT_DIR, "dataset_gen", f"{name}.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return out_path


def main() -> None:
    random.seed(20260423)
    for name, cfg in GROUPS.items():
        nodes_min, nodes_max = cfg["nodes_range"]
        out_path = build_group_csv(
            name=name,
            max_depth=cfg["max_depth"],
            nodes_min=nodes_min,
            nodes_max=nodes_max,
            count=cfg["count"],
        )
        print(f"{name}: {out_path}")


if __name__ == "__main__":
    main()
