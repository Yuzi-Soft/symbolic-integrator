from __future__ import annotations

import csv
import os
import sys
from dataclasses import dataclass


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from differentiator import differentiate
from expr_parser import parse_expr
from simplify import simplify


@dataclass
class Case:
    name: str
    text: str
    expected_pretty: str


def build_cases() -> list[Case]:
    return [
        Case(
            name="linear_sum",
            text="((3 * x) + Cos(x))",
            expected_pretty="((3 * x) + Cos(x))",
        ),
        Case(
            name="negative_fraction_power",
            text="((x ^ -7/2) + (x ^ 3))",
            expected_pretty="((x ^ -7/2) + (x ^ 3))",
        ),
        Case(
            name="log_rational_base",
            text="Log_4/5((-1/3 + (2 * x)))",
            expected_pretty="Log_4/5((-1/3 + (2 * x)))",
        ),
        Case(
            name="nested_functions",
            text="Sin(Ln((4 * (x ^ 3))))",
            expected_pretty="Sin(Ln((4 * (x ^ 3))))",
        ),
    ]


def run_parser_cases() -> tuple[int, int]:
    passed = 0
    cases = build_cases()

    for idx, case in enumerate(cases, start=1):
        print(f"[Parser Case {idx}] {case.name}")
        print(f"IN : {case.text}")
        parsed = parse_expr(case.text)
        out = parsed.pretty()
        print(f"OUT: {out}")
        print(f"EXPECT: {case.expected_pretty}")
        if out == case.expected_pretty:
            print("RESULT: PASS")
            passed += 1
        else:
            print("RESULT: FAIL")
        print("-" * 72)

    return passed, len(cases)


def run_hard_verification(limit: int = 100) -> tuple[int, int]:
    path = os.path.join(ROOT_DIR, "dataset_gen", "hard.csv")
    passed = 0
    total = 0

    with open(path, newline="", encoding="utf-8") as f:
        for row_index, row in enumerate(csv.reader(f), start=1):
            if total >= limit:
                break

            integrand_text = row[0].strip()
            antiderivative_text = row[1].strip()
            print(f"[Hard Row {row_index}]")
            integrand = None
            recovered = None

            try:
                integrand = simplify(parse_expr(integrand_text))
                antiderivative = parse_expr(antiderivative_text)
                recovered = simplify(differentiate(antiderivative))
                ok = recovered == integrand
            except Exception as exc:  # noqa: BLE001
                print(f"OUT: EXCEPTION {type(exc).__name__}: {exc}")
                ok = False

            if ok:
                print("RESULT: PASS")
                passed += 1
            else:
                print("RESULT: FAIL")
                if recovered is not None and integrand is not None:
                    print(f"RECOVERED: {recovered.pretty()}")
                    print(f"EXPECT   : {integrand.pretty()}")

            print("-" * 72)
            total += 1

    return passed, total


def run_cases() -> int:
    parser_passed, parser_total = run_parser_cases()
    hard_passed, hard_total = run_hard_verification(limit=100)

    passed = parser_passed + hard_passed
    total = parser_total + hard_total
    failed = total - passed
    print(f"SUMMARY: total={total}, passed={passed}, failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_cases())
