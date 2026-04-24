from __future__ import annotations

import os
import random
import sys
from dataclasses import dataclass


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from AST_nodes import Const, Var
from differentiator import differentiate
from generator import generate, generate_leaf, number_split, random_select, select_operation
from simplify import simplify


@dataclass
class Case:
    name: str
    runner: object


def case_number_split_basic() -> tuple[bool, str]:
    random.seed(0)
    parts = number_split(10, 4)
    ok = len(parts) == 4 and sum(parts) == 10 and all(part > 0 for part in parts)
    return ok, f"parts={parts}"


def case_number_split_all_ones() -> tuple[bool, str]:
    random.seed(1)
    parts = number_split(8, 8)
    ok = parts == [1] * 8
    return ok, f"parts={parts}"


def case_random_select_weighted() -> tuple[bool, str]:
    random.seed(2)
    picks = [random_select({"a": 1.0, "b": 0.0, "c": 0.0}) for _ in range(20)]
    ok = all(pick == "a" for pick in picks)
    return ok, f"picks={picks[:5]}..."


def case_select_operation_root() -> tuple[bool, str]:
    random.seed(3)
    picks = [select_operation(1) for _ in range(20)]
    ok = all(pick == "add" for pick in picks)
    return ok, f"picks={picks[:5]}..."


def case_generate_bounds() -> tuple[bool, str]:
    random.seed(4)
    expr = generate(max_depth=4, nodes=9)
    depth_ok = expr.depth() <= 4
    nodes_ok = expr.node_count() <= 9
    return depth_ok and nodes_ok, f"depth={expr.depth()}, nodes={expr.node_count()}, expr={expr.pretty()}"


def case_generate_bounds_many() -> tuple[bool, str]:
    for seed in range(50):
        random.seed(seed)
        expr = generate(max_depth=5, nodes=11)
        if expr.depth() > 5 or expr.node_count() > 11:
            return False, f"seed={seed}, depth={expr.depth()}, nodes={expr.node_count()}, expr={expr.pretty()}"
    return True, "50 seeds checked"


def case_generate_diff_simplify_pipeline() -> tuple[bool, str]:
    for seed in range(40):
        random.seed(seed + 100)
        expr = generate(max_depth=5, nodes=11)
        out = simplify(differentiate(expr))
        _ = out.pretty()
    return True, "40 generated expressions differentiated and simplified"


def case_generate_expr_type() -> tuple[bool, str]:
    random.seed(9)
    expr = generate(max_depth=4, nodes=9)
    ok = expr.is_var_expr() or expr.is_const_expr()
    return ok, f"type={expr.type}, pretty={expr.pretty()}"


def case_leaf_budget_falls_back_to_x() -> tuple[bool, str]:
    random.seed(10)
    expr = generate_leaf(Var("x"), max_depth=1, cur_depth=1, nodes=1)
    ok = isinstance(expr, Var)
    return ok, f"type={expr.type}, pretty={expr.pretty()}"


def case_leaf_never_bare_const() -> tuple[bool, str]:
    for seed in range(30):
        random.seed(seed + 200)
        expr = generate_leaf(Var("x"), max_depth=5, cur_depth=1, nodes=5)
        if isinstance(expr, Const):
            return False, f"seed={seed}, expr={expr.pretty()}"
    return True, "30 terminal leaves checked"


def build_cases() -> list[Case]:
    return [
        Case(name="number_split_basic", runner=case_number_split_basic),
        Case(name="number_split_all_ones", runner=case_number_split_all_ones),
        Case(name="random_select_weighted", runner=case_random_select_weighted),
        Case(name="select_operation_root", runner=case_select_operation_root),
        Case(name="generate_bounds", runner=case_generate_bounds),
        Case(name="generate_bounds_many", runner=case_generate_bounds_many),
        Case(name="generate_diff_simplify_pipeline", runner=case_generate_diff_simplify_pipeline),
        Case(name="generate_expr_type", runner=case_generate_expr_type),
        Case(name="leaf_budget_falls_back_to_x", runner=case_leaf_budget_falls_back_to_x),
        Case(name="leaf_never_bare_const", runner=case_leaf_never_bare_const),
    ]


def run_cases() -> int:
    cases = build_cases()
    passed = 0

    for idx, case in enumerate(cases, start=1):
        print(f"[Case {idx}] {case.name}")
        ok, detail = case.runner()  # type: ignore
        print(f"DETAIL: {detail}")
        if ok:
            print("RESULT: PASS")
            passed += 1
        else:
            print("RESULT: FAIL")
        print("-" * 72)

    total = len(cases)
    failed = total - passed
    print(f"SUMMARY: total={total}, passed={passed}, failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_cases())
