from __future__ import annotations

import csv
import math
import os
import random
import re
import sys
from fractions import Fraction


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from AST_nodes import Const, Expr
from differentiator import differentiate
from generator import generate
from simplify import simplify


GROUPS = {
    "simple": {
        "max_depth": 4,
        "nodes_range": (6, 12),
        "count": 1000,
        "pool_count": 1500,
        "trim_head": 250,
        "trim_tail": 250,
        "min_derivative_nodes": 3,
        "require_advanced_expr": False,
        "require_nonzero_second_derivative": False,
        "max_integrand_repeats": 2,
    },
    "medium": {
        "max_depth": 5,
        "nodes_range": (11, 19),
        "count": 1000,
        "pool_count": 1500,
        "trim_head": 250,
        "trim_tail": 250,
        "min_derivative_nodes": 6,
        "require_advanced_expr": True,
        "require_nonzero_second_derivative": False,
        "max_integrand_repeats": 3,
    },
    "hard": {
        "max_depth": 6,
        "nodes_range": (18, 28),
        "count": 1000,
        "pool_count": 1500,
        "trim_head": 500,
        "trim_tail": 0,
        "min_derivative_nodes": 10,
        "require_advanced_expr": True,
        "require_nonzero_second_derivative": True,
        "max_integrand_repeats": 2,
    },
}


ADVANCED_TYPES = {"Mul", "Div", "Pow", "Sin", "Cos", "Ln", "Log"}


def walk(expr: Expr) -> list[Expr]:
    out = [expr]
    for child in expr.children:
        out.extend(walk(child))
    return out


def has_advanced_structure(expr: Expr) -> bool:
    return any(node.type in ADVANCED_TYPES for node in walk(expr))


def normalize_constants(s: str) -> str:
    normalized = re.sub(r"-?\d+(?:/\d+)?", "CONST", s)
    normalized = normalized.replace("pi", "CONST_PI").replace("e", "CONST_E")
    return normalized


def difficulty_score(expr_text: str) -> float:
    op_count = sum(expr_text.count(token) for token in ("+", "*", "/", "^", "Sin", "Cos", "Ln", "Log_"))
    max_depth = max_parenthesis_depth(expr_text)
    pow_count = expr_text.count("^")
    div_count = expr_text.count("/")
    trig_count = expr_text.count("Sin(") + expr_text.count("Cos(")
    log_count = expr_text.count("Ln(") + expr_text.count("Log_")
    add_terms = top_level_add_terms(expr_text)
    return op_count + 0.5 * max_depth + pow_count + 0.8 * div_count + trig_count + 1.2 * log_count + 0.5 * add_terms


def max_parenthesis_depth(expr_text: str) -> int:
    depth = 0
    max_depth = 0
    for ch in expr_text:
        if ch == "(":
            depth += 1
            max_depth = max(max_depth, depth)
        elif ch == ")":
            depth -= 1
    return max_depth


def top_level_add_terms(expr_text: str) -> int:
    text = strip_wrapping_parentheses(expr_text.strip())
    depth = 0
    plus_count = 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "+" and depth == 0:
            plus_count += 1
    if plus_count == 0:
        return 1
    return plus_count + 1


def strip_wrapping_parentheses(expr_text: str) -> str:
    text = expr_text
    while is_fully_wrapped(text):
        text = text[1:-1].strip()
    return text


def is_fully_wrapped(expr_text: str) -> bool:
    if len(expr_text) < 2 or expr_text[0] != "(" or expr_text[-1] != ")":
        return False
    depth = 0
    for index, ch in enumerate(expr_text):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if depth == 0 and index < len(expr_text) - 1:
            return False
    return depth == 0


def trim_by_difficulty(
    rows: list[tuple[str, str]],
    final_count: int,
    trim_head: int,
    trim_tail: int,
) -> list[tuple[str, str]]:
    if trim_head < 0 or trim_tail < 0:
        raise ValueError("trim counts must be non-negative")
    if len(rows) - trim_head - trim_tail != final_count:
        raise ValueError(
            f"trim plan must keep exactly {final_count} rows, got pool={len(rows)}, "
            f"trim_head={trim_head}, trim_tail={trim_tail}"
        )

    ranked = sorted(enumerate(rows), key=lambda item: (difficulty_score(item[1][0]), item[0]))
    kept = ranked[trim_head : len(ranked) - trim_tail if trim_tail else len(ranked)]
    return [row for _, row in kept]


def const_rational_value(expr: Expr) -> Fraction | None:
    if isinstance(expr, Const) and isinstance(expr.value, Fraction):
        return expr.value
    return None


def has_invalid_domain_node(expr: Expr) -> bool:
    if hasattr(expr, "children"):
        if expr.type == "Div":
            denominator = simplify(expr.children[1])
            den_value = const_rational_value(denominator)
            if den_value == 0:
                return True
        if expr.type == "Ln":
            child = simplify(expr.children[0])
            child_value = const_rational_value(child)
            if child_value is not None and child_value <= 0:
                return True
        if expr.type == "Log":
            base = simplify(expr.children[0])
            argument = simplify(expr.children[1])
            base_value = const_rational_value(base)
            argument_value = const_rational_value(argument)
            if base_value is not None and (base_value <= 0 or base_value == 1):
                return True
            if argument_value is not None and argument_value <= 0:
                return True
        if expr.type == "Pow":
            base = simplify(expr.children[0])
            exponent = simplify(expr.children[1])
            base_value = const_rational_value(base)
            exponent_value = const_rational_value(exponent)
            if (
                base_value is not None
                and exponent_value is not None
                and base_value < 0
                and exponent_value.denominator != 1
            ):
                return True

    for child in expr.children:
        if has_invalid_domain_node(child):
            return True
    return False


def finite_on_probe_points(expr: Expr, min_valid: int = 2) -> bool:
    valid = 0
    for x in (0.7, 1.1, 1.7, 2.3, 3.1):
        try:
            value = expr.eval(x)
            if isinstance(value, float) and math.isfinite(value):
                valid += 1
        except Exception:
            continue
    return valid >= min_valid


def is_domain_valid(expr: Expr, derivative: Expr) -> bool:
    if has_invalid_domain_node(expr):
        return False
    if has_invalid_domain_node(derivative):
        return False
    if not finite_on_probe_points(expr):
        return False
    if not finite_on_probe_points(derivative):
        return False
    return True


def uniform_node_plan(nodes_min: int, nodes_max: int, count: int) -> list[int]:
    values = list(range(nodes_min, nodes_max + 1))
    per_value = count // len(values)
    remainder = count % len(values)
    plan: list[int] = []
    for idx, value in enumerate(values):
        c = per_value + (1 if idx < remainder else 0)
        plan.extend([value] * c)
    random.shuffle(plan)
    return plan


def build_group_csv(
    name: str,
    max_depth: int,
    nodes_min: int,
    nodes_max: int,
    count: int,
    pool_count: int,
    trim_head: int,
    trim_tail: int,
    min_derivative_nodes: int,
    require_advanced_expr: bool,
    require_nonzero_second_derivative: bool,
    max_integrand_repeats: int,
) -> str:
    rows: list[tuple[str, str]] = []
    seen_signatures: set[tuple[str, str]] = set()
    seen_rows: set[tuple[str, str]] = set()
    integrand_counts: dict[str, int] = {}
    node_plan = uniform_node_plan(nodes_min, nodes_max, pool_count)
    rejected = 0

    for target_nodes in node_plan:
        tries = 0
        while True:
            tries += 1
            if tries > 6000:
                break

            raw_expr = generate(max_depth=max_depth, nodes=target_nodes)
            expr = simplify(raw_expr)
            if not expr.is_var_expr():
                rejected += 1
                continue

            if require_advanced_expr and not has_advanced_structure(expr):
                rejected += 1
                continue

            derivative = simplify(differentiate(expr))
            if isinstance(derivative, Const):
                rejected += 1
                continue

            if derivative.node_count() < min_derivative_nodes:
                rejected += 1
                continue

            if require_nonzero_second_derivative:
                second = simplify(differentiate(derivative))
                if isinstance(second, Const) and second.value == 0:
                    rejected += 1
                    continue

            if not is_domain_valid(expr, derivative):
                rejected += 1
                continue

            pair = (derivative.pretty(), expr.pretty())
            if pair in seen_rows:
                rejected += 1
                continue
            signature = (normalize_constants(pair[0]), normalize_constants(pair[1]))
            if signature in seen_signatures and tries < 300:
                rejected += 1
                continue

            # Early tries enforce diversity harder; later tries gradually relax
            # to ensure the generator can finish large datasets.
            effective_max_repeats = max_integrand_repeats + (tries // 1500)
            if integrand_counts.get(pair[0], 0) >= effective_max_repeats:
                rejected += 1
                continue

            seen_signatures.add(signature)
            seen_rows.add(pair)
            integrand_counts[pair[0]] = integrand_counts.get(pair[0], 0) + 1
            rows.append(pair)
            break

    while len(rows) < pool_count:
        target_nodes = random.randint(nodes_min, nodes_max)
        tries = 0
        while True:
            tries += 1
            if tries > 6000:
                raw_expr = generate(max_depth=max_depth, nodes=target_nodes)
                expr = simplify(raw_expr)
                if not expr.is_var_expr():
                    rejected += 1
                    continue
                derivative = simplify(differentiate(expr))
                if isinstance(derivative, Const):
                    rejected += 1
                    continue
                if not is_domain_valid(expr, derivative):
                    rejected += 1
                    continue
                pair = (derivative.pretty(), expr.pretty())
                if pair in seen_rows:
                    rejected += 1
                    continue
                rows.append(pair)
                seen_rows.add(pair)
                break

            raw_expr = generate(max_depth=max_depth, nodes=target_nodes)
            expr = simplify(raw_expr)
            if not expr.is_var_expr():
                rejected += 1
                continue

            if require_advanced_expr and not has_advanced_structure(expr):
                rejected += 1
                continue

            derivative = simplify(differentiate(expr))
            if isinstance(derivative, Const):
                rejected += 1
                continue

            if derivative.node_count() < min_derivative_nodes:
                rejected += 1
                continue

            if require_nonzero_second_derivative:
                second = simplify(differentiate(derivative))
                if isinstance(second, Const) and second.value == 0:
                    rejected += 1
                    continue

            if not is_domain_valid(expr, derivative):
                rejected += 1
                continue

            pair = (derivative.pretty(), expr.pretty())
            if pair in seen_rows:
                rejected += 1
                continue
            signature = (normalize_constants(pair[0]), normalize_constants(pair[1]))
            if signature in seen_signatures and tries < 300:
                rejected += 1
                continue

            effective_max_repeats = max_integrand_repeats + (tries // 1500)
            if integrand_counts.get(pair[0], 0) >= effective_max_repeats:
                rejected += 1
                continue

            seen_signatures.add(signature)
            seen_rows.add(pair)
            integrand_counts[pair[0]] = integrand_counts.get(pair[0], 0) + 1
            rows.append(pair)
            break

    pool_size = len(rows)
    rows = trim_by_difficulty(rows, count, trim_head, trim_tail)

    out_path = os.path.join(ROOT_DIR, "dataset_gen", f"{name}.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(
        f"{name}: pool={pool_size}, generated={len(rows)}, rejected={rejected}, "
        f"unique_signatures={len(seen_signatures)}, trim_head={trim_head}, trim_tail={trim_tail}"
    )
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
            pool_count=cfg["pool_count"],
            trim_head=cfg["trim_head"],
            trim_tail=cfg["trim_tail"],
            min_derivative_nodes=cfg["min_derivative_nodes"],
            require_advanced_expr=cfg["require_advanced_expr"],
            require_nonzero_second_derivative=cfg["require_nonzero_second_derivative"],
            max_integrand_repeats=cfg["max_integrand_repeats"],
        )
        print(f"{name}: {out_path}")


if __name__ == "__main__":
    main()
