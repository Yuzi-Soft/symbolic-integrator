from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from AST_nodes import Add, Const, Div, Mul, Pow, Var
from algebra_basis import rebuild_term, split_term


@dataclass
class Case:
    name: str
    expr: object
    expected_coefficient: str
    expected_basis: str
    expected_rebuilt: Optional[str] = None


def build_cases() -> list[Case]:
    x = Var("x")
    sqrt_e = Pow(Const("e"), Div(Const(1), Const(2)))

    return [
        Case(
            name="rational_constant",
            expr=Const(5),
            expected_coefficient="5",
            expected_basis="1",
            expected_rebuilt="5",
        ),
        Case(
            name="special_constant_product",
            expr=Mul([Const(6), Const("pi"), Const("e")]),
            expected_coefficient="(6 * pi * e)",
            expected_basis="1",
            expected_rebuilt="(6 * pi * e)",
        ),
        Case(
            name="const_over_variable",
            expr=Div(Const("pi"), x),
            expected_coefficient="pi",
            expected_basis="(1 / x)",
            expected_rebuilt="(pi * (1 / x))",
        ),
        Case(
            name="pi_x_over_2",
            expr=Div(Mul([Const("pi"), x]), Const(2)),
            expected_coefficient="(pi / 2)",
            expected_basis="x",
            expected_rebuilt="((pi / 2) * x)",
        ),
        Case(
            name="two_pi_over_three_x",
            expr=Div(Mul([Const(2), Const("pi")]), Mul([Const(3), x])),
            expected_coefficient="((2 * pi) / 3)",
            expected_basis="(1 / x)",
            expected_rebuilt="(((2 * pi) / 3) * (1 / x))",
        ),
        Case(
            name="sqrt_e_pi_x",
            expr=Mul([sqrt_e, Const("pi"), x]),
            expected_coefficient="((e ^ (1 / 2)) * pi)",
            expected_basis="x",
            expected_rebuilt="(((e ^ (1 / 2)) * pi) * x)",
        ),
        Case(
            name="non_monomial_term",
            expr=Add([x, Const(1)]),
            expected_coefficient="1",
            expected_basis="(x + 1)",
            expected_rebuilt="(x + 1)",
        ),
    ]


def run_cases() -> int:
    cases = build_cases()
    passed = 0

    for idx, case in enumerate(cases, start=1):
        print(f"[Case {idx}] {case.name}")
        print(f"IN   : {case.expr.pretty()}")

        coefficient, basis = split_term(case.expr)
        rebuilt = rebuild_term(coefficient, basis)

        print(f"COEF : {coefficient.pretty()}")
        print(f"BASIS: {basis.pretty()}")
        print(f"OUT  : {rebuilt.pretty()}")

        result = (
            coefficient.pretty() == case.expected_coefficient
            and basis.pretty() == case.expected_basis
            and rebuilt.pretty() == (case.expected_rebuilt or case.expr.pretty())
        )

        print(f"EXPECT COEF : {case.expected_coefficient}")
        print(f"EXPECT BASIS: {case.expected_basis}")
        print(f"EXPECT OUT  : {case.expected_rebuilt or case.expr.pretty()}")
        print(f"RESULT: {'PASS' if result else 'FAIL'}")

        if result:
            passed += 1

        print("-" * 72)

    total = len(cases)
    failed = total - passed
    print(f"SUMMARY: total={total}, passed={passed}, failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_cases())
