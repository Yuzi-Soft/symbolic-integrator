from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from fractions import Fraction


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from AST_nodes import Add, Const, Div, Mul, Pow, Sin, Var
from simplify import simplify


@dataclass
class Case:
    name: str
    expr: object
    expected_pretty: str


def build_cases() -> list[Case]:
    x = Var("x")
    sqrt_2 = Pow(Const(2), Div(Const(1), Const(2)))

    return [
        Case(
            name="add_zero",
            expr=Add([x, Const(0)]),
            expected_pretty="x",
        ),
        Case(
            name="mul_one",
            expr=Mul([x, Const(1)]),
            expected_pretty="x",
        ),
        Case(
            name="mul_zero",
            expr=Mul([x, Const(0)]),
            expected_pretty="0",
        ),
        Case(
            name="div_by_const",
            expr=Div(Mul([Const("pi"), x]), Const(2)),
            expected_pretty="(1/2 * pi * x)",
        ),
        Case(
            name="like_terms",
            expr=Add([Mul([Const(2), x]), Mul([Const(3), x])]),
            expected_pretty="(5 * x)",
        ),
        Case(
            name="factor_common_pi",
            expr=Add(
                [
                    Mul([Const(3), Sin(Const(3)), Const("pi")]),
                    Mul([Const(1), Sin(Const(4)), Const("pi")]),
                    Mul([Const(Fraction(-1, 2)), Sin(Const(3)), Const("pi")]),
                ]
            ),
            expected_pretty="(((5/2 * Sin(3)) + Sin(4)) * pi)",
        ),
        Case(
            name="combine_pi_x_terms",
            expr=Add(
                [
                    Div(Mul([Const("pi"), x]), Const(2)),
                    Div(Mul([Const(3), Const("pi"), x]), Const(4)),
                ]
            ),
            expected_pretty="(5/4 * pi * x)",
        ),
        Case(
            name="constant_common_pi",
            expr=Add([Mul([Const(2), Const("pi")]), Mul([Const(3), sqrt_2, Const("pi")]), Mul([Const(4), Const("pi")])]),
            expected_pretty="((6 + (3 * (2 ^ 1/2))) * pi)",
        ),
    ]


def run_cases() -> int:
    cases = build_cases()
    passed = 0

    for idx, case in enumerate(cases, start=1):
        print(f"[Case {idx}] {case.name}")
        print(f"IN : {case.expr.pretty()}")  # type: ignore

        out = simplify(case.expr)  # type: ignore
        out_pretty = out.pretty()

        print(f"OUT: {out_pretty}")
        print(f"EXPECT: {case.expected_pretty}")

        if out_pretty == case.expected_pretty:
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
