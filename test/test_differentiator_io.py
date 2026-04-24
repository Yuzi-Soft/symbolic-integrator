from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional, Type


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from AST_nodes import Add, Const, Div, Ln, Log, Mul, Pow, Sin, Var
from differentiator import differentiate


@dataclass
class Case:
    name: str
    expr: object
    expected_pretty: Optional[str] = None
    expected_exception: Optional[Type[BaseException]] = None


def build_cases() -> list[Case]:
    x = Var("x")
    return [
        Case(
            name="const",
            expr=Const(5),
            expected_pretty="0",
        ),
        Case(
            name="var",
            expr=x,
            expected_pretty="1",
        ),
        Case(
            name="add",
            expr=Add([x, Const(3)]),
            expected_pretty="(1 + 0)",
        ),
        Case(
            name="mul",
            expr=Mul([x, Sin(x)]),
            expected_pretty="((1 * Sin(x)) + (x * (Cos(x) * 1)))",
        ),
        Case(
            name="div",
            expr=Div(Sin(x), x),
            expected_pretty="((((Cos(x) * 1) * x) + (-1 * Sin(x) * 1)) / (x ^ 2))",
        ),
        Case(
            name="pow_x_2",
            expr=Pow(x, Const(2)),
            expected_pretty="(2 * (x ^ (2 + -1)) * 1)",
        ),
        Case(
            name="pow_2_x",
            expr=Pow(Const(2), x),
            expected_pretty="((2 ^ x) * Ln(2) * 1)",
        ),
        Case(
            name="pow_x_pi_over_2",
            expr=Pow(x, Div(Const("pi"), Const(2))),
            expected_pretty="((pi / 2) * (x ^ ((pi / 2) + -1)) * 1)",
        ),
        Case(
            name="pow_6_pi_e_x",
            expr=Pow(Mul([Const(6), Const("pi"), Const("e")]), x),
            expected_pretty="(((6 * pi * e) ^ x) * Ln((6 * pi * e)) * 1)",
        ),
        Case(
            name="const_expr_derivative_zero",
            expr=Mul([Pow(Const("e"), Div(Const(1), Const(2))), Const("pi")]),
            expected_pretty="0",
        ),
        Case(
            name="pow_x_x_unsupported",
            expr=Pow(x, x),
            expected_exception=NotImplementedError,
        ),
        Case(
            name="ln",
            expr=Ln(Add([x, Const(1)])),
            expected_pretty="((1 + 0) / (x + 1))",
        ),
        Case(
            name="log",
            expr=Log(Const(10), x),
            expected_pretty="(1 / (x * Ln(10)))",
        ),
    ]


def run_cases() -> int:
    cases = build_cases()
    passed = 0

    for idx, case in enumerate(cases, start=1):
        print(f"[Case {idx}] {case.name}")
        print(f"IN : {case.expr.pretty()}") # type: ignore

        try:
            out = differentiate(case.expr) # type: ignore
            out_pretty = out.pretty()
            print(f"OUT: {out_pretty}")

            if case.expected_exception is not None:
                print(f"EXPECT: exception {case.expected_exception.__name__}")
                print("RESULT: FAIL")
            elif out_pretty == case.expected_pretty:
                print(f"EXPECT: {case.expected_pretty}")
                print("RESULT: PASS")
                passed += 1
            else:
                print(f"EXPECT: {case.expected_pretty}")
                print("RESULT: FAIL")

        except Exception as exc:  # noqa: BLE001
            print(f"OUT: EXCEPTION {type(exc).__name__}: {exc}")
            if case.expected_exception is not None and isinstance(exc, case.expected_exception):
                print(f"EXPECT: exception {case.expected_exception.__name__}")
                print("RESULT: PASS")
                passed += 1
            else:
                if case.expected_exception is not None:
                    print(f"EXPECT: exception {case.expected_exception.__name__}")
                else:
                    print(f"EXPECT: {case.expected_pretty}")
                print("RESULT: FAIL")

        print("-" * 72)

    total = len(cases)
    failed = total - passed
    print(f"SUMMARY: total={total}, passed={passed}, failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_cases())
