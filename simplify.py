from __future__ import annotations

from fractions import Fraction

from AST_nodes import Add, Const, Cos, Div, Expr, Ln, Log, Mul, Pow, Sin, Var
from algebra_basis import ONE, ZERO, basis_key, build_product, build_sum, is_one, is_zero


_TYPE_ORDER = {
    "Const": 0,
    "Var": 1,
    "Add": 2,
    "Mul": 3,
    "Div": 4,
    "Pow": 5,
    "Sin": 6,
    "Cos": 7,
    "Ln": 8,
    "Log": 9,
}


def simplify(expr: Expr) -> Expr:
    current = expr
    while True:
        simplified = simplify_once(current)
        if simplified == current:
            return simplified
        current = simplified


def simplify_once(expr: Expr) -> Expr:
    if isinstance(expr, (Const, Var)):
        return expr

    if isinstance(expr, Add):
        return simplify_add([simplify(term) for term in expr.children])

    if isinstance(expr, Mul):
        return simplify_mul([simplify(factor) for factor in expr.children])

    if isinstance(expr, Div):
        numerator = simplify(expr.children[0])
        denominator = simplify(expr.children[1])
        return simplify_div(numerator, denominator)

    if isinstance(expr, Pow):
        base = simplify(expr.children[0])
        exponent = simplify(expr.children[1])
        return simplify_pow(base, exponent)

    if isinstance(expr, Sin):
        child = simplify(expr.children[0])
        return Sin(child)

    if isinstance(expr, Cos):
        child = simplify(expr.children[0])
        return Cos(child)

    if isinstance(expr, Ln):
        child = simplify(expr.children[0])
        return Ln(child)

    if isinstance(expr, Log):
        base = simplify(expr.children[0])
        argument = simplify(expr.children[1])
        return Log(base, argument)

    return expr


def simplify_add(terms: list[Expr]) -> Expr:
    pending = list(terms)
    flat_terms: list[Expr] = []

    while pending:
        term = pending.pop(0)
        if is_zero(term):
            continue
        if isinstance(term, Add):
            pending = list(term.children) + pending
            continue
        flat_terms.append(term)

    grouped: dict[tuple, tuple[Fraction, list[Expr]]] = {}

    for term in flat_terms:
        coefficient, factors = normalize_term(term)
        if coefficient == 0:
            continue

        key = tuple(basis_key(factor) for factor in factors)
        if key in grouped:
            previous_coefficient, previous_factors = grouped[key]
            grouped[key] = (previous_coefficient + coefficient, previous_factors)
        else:
            grouped[key] = (coefficient, factors)

    normalized_terms: list[tuple[Fraction, list[Expr]]] = []
    for coefficient, factors in grouped.values():
        if coefficient != 0:
            normalized_terms.append((coefficient, factors))

    if len(normalized_terms) == 0:
        return ZERO

    factored = factor_common_factors(normalized_terms)
    if factored is not None:
        return factored

    rebuilt_terms = [build_term(coefficient, factors) for coefficient, factors in normalized_terms]
    rebuilt_terms.sort(key=expr_sort_key)
    return build_sum(rebuilt_terms)


def simplify_mul(factors: list[Expr]) -> Expr:
    pending = list(factors)
    flat_factors: list[Expr] = []
    rational_coefficient = Fraction(1, 1)

    while pending:
        factor = pending.pop(0)
        if is_zero(factor):
            return ZERO
        if isinstance(factor, Mul):
            pending = list(factor.children) + pending
            continue
        if is_one(factor):
            continue
        if is_rational_const(factor):
            rational_coefficient *= rational_const_value(factor)
            continue
        flat_factors.append(factor)

    if rational_coefficient == 0:
        return ZERO

    flat_factors.sort(key=factor_sort_key)

    result_factors: list[Expr] = []
    if rational_coefficient != 1 or len(flat_factors) == 0:
        result_factors.append(Const(rational_coefficient))
    result_factors.extend(flat_factors)

    return build_product(result_factors)


def simplify_div(numerator: Expr, denominator: Expr) -> Expr:
    if is_zero(numerator):
        return ZERO
    if is_one(denominator):
        return numerator

    if is_rational_const(numerator) and is_rational_const(denominator):
        numerator_value = rational_const_value(numerator)
        denominator_value = rational_const_value(denominator)
        if denominator_value != 0:
            return Const(numerator_value / denominator_value)

    numerator_coefficient, numerator_factors = normalize_term(numerator)
    denominator_coefficient, denominator_factors = normalize_term(denominator)

    if denominator_coefficient == 0:
        return Div(numerator, denominator)

    rational_coefficient = numerator_coefficient / denominator_coefficient
    result_factors = list(numerator_factors)

    if len(denominator_factors) > 0:
        denominator_basis = build_product(denominator_factors)
        result_factors.append(Div(ONE, denominator_basis))

    if len(result_factors) == 0:
        return Const(rational_coefficient)

    return simplify_mul(([Const(rational_coefficient)] if rational_coefficient != 1 else []) + result_factors)


def simplify_pow(base: Expr, exponent: Expr) -> Expr:
    if is_rational_const(exponent):
        exponent_value = rational_const_value(exponent)
        if exponent_value == 0:
            return ONE
        if exponent_value == 1:
            return base

    if is_rational_const(base):
        base_value = rational_const_value(base)
        exponent_value_opt: Fraction | None
        if is_rational_const(exponent):
            exponent_value_opt = rational_const_value(exponent)
        else:
            exponent_value_opt = None

        if base_value == 0 and exponent_value_opt is not None and exponent_value_opt > 0:
            return ZERO
        if base_value == 1:
            return ONE

    if is_rational_const(base) and is_rational_const(exponent):
        base_value = rational_const_value(base)
        exponent_value = rational_const_value(exponent)
        if exponent_value.denominator == 1:
            integer_exponent = exponent_value.numerator
            if base_value != 0 or integer_exponent >= 0:
                return Const(base_value ** integer_exponent)

    return Pow(base, exponent)


def normalize_term(term: Expr) -> tuple[Fraction, list[Expr]]:
    if isinstance(term, Mul):
        factor_list = list(term.children)
    else:
        factor_list = [term]

    rational_coefficient = Fraction(1, 1)
    basis_factors: list[Expr] = []

    for factor in factor_list:
        if is_rational_const(factor):
            rational_coefficient *= rational_const_value(factor)
        else:
            basis_factors.append(factor)

    basis_factors.sort(key=factor_sort_key)
    return rational_coefficient, basis_factors


def build_term(coefficient: Fraction, factors: list[Expr]) -> Expr:
    if coefficient == 0:
        return ZERO

    result_factors: list[Expr] = []
    if coefficient != 1 or len(factors) == 0:
        result_factors.append(Const(coefficient))
    result_factors.extend(factors)
    return build_product(result_factors)


def factor_common_factors(terms: list[tuple[Fraction, list[Expr]]]) -> Expr | None:
    if len(terms) < 2:
        return None

    common_factors = common_factor_list([factors for _, factors in terms])
    if len(common_factors) == 0:
        return None

    residual_terms: list[Expr] = []
    for coefficient, factors in terms:
        residual_factors = remove_factor_occurrences(factors, common_factors)
        residual_terms.append(build_term(coefficient, residual_factors))

    residual_expr = simplify_add(residual_terms)
    return build_product([residual_expr] + common_factors)


def common_factor_list(factor_lists: list[list[Expr]]) -> list[Expr]:
    if len(factor_lists) == 0:
        return []

    counts, representatives = factor_count_map(factor_lists[0])

    for factors in factor_lists[1:]:
        next_counts, _ = factor_count_map(factors)
        for key in list(counts):
            counts[key] = min(counts[key], next_counts.get(key, 0))
            if counts[key] == 0:
                del counts[key]

    common_factors: list[Expr] = []
    for key, factor in representatives.items():
        if key in counts:
            common_factors.extend([factor] * counts[key])

    common_factors.sort(key=factor_sort_key)
    return common_factors


def factor_count_map(factors: list[Expr]) -> tuple[dict[tuple, int], dict[tuple, Expr]]:
    counts: dict[tuple, int] = {}
    representatives: dict[tuple, Expr] = {}

    for factor in factors:
        key = basis_key(factor)
        counts[key] = counts.get(key, 0) + 1
        representatives[key] = factor

    return counts, representatives


def remove_factor_occurrences(factors: list[Expr], to_remove: list[Expr]) -> list[Expr]:
    remaining = list(factors)

    for factor in to_remove:
        for index, candidate in enumerate(remaining):
            if candidate == factor:
                remaining.pop(index)
                break

    return remaining


def factor_sort_key(expr: Expr):
    if isinstance(expr, Add):
        return (-1, expr_sort_key(expr))
    if expr.is_const_expr():
        return (0, const_factor_sort_key(expr))
    return (1, expr_sort_key(expr))


def const_factor_sort_key(expr: Expr):
    if is_rational_const(expr):
        return (0, float(rational_const_value(expr)))

    if isinstance(expr, Const):
        if expr.is_e():
            return (2, 0)
        if expr.is_pi():
            return (2, 1)

    if isinstance(expr, Pow) and is_half_power(expr):
        return (1, 0, expr_sort_key(expr.children[0]))
    if isinstance(expr, Sin):
        return (1, 1, expr_sort_key(expr.children[0]))
    if isinstance(expr, Cos):
        return (1, 2, expr_sort_key(expr.children[0]))
    if isinstance(expr, Ln):
        return (1, 3, expr_sort_key(expr.children[0]))
    if isinstance(expr, Log):
        return (1, 4, expr_sort_key(expr.children[0]), expr_sort_key(expr.children[1]))

    return (1, 9, expr_sort_key(expr))


def expr_sort_key(expr: Expr):
    base = (_TYPE_ORDER.get(expr.type, 99),)

    if isinstance(expr, Const):
        if is_rational_const(expr):
            return base + (0, float(expr.value))
        if expr.is_e():
            return base + (1, 0)
        if expr.is_pi():
            return base + (1, 1)
        return base + (2,)

    if isinstance(expr, Var):
        return base + (expr.value,)

    return base + tuple(expr_sort_key(child) for child in expr.children)


def is_rational_const(expr: Expr) -> bool:
    return isinstance(expr, Const) and isinstance(expr.value, Fraction)


def rational_const_value(expr: Expr) -> Fraction:
    assert isinstance(expr, Const)
    assert isinstance(expr.value, Fraction)
    return expr.value


def is_half_power(expr: Expr) -> bool:
    return (
        isinstance(expr, Pow)
        and is_rational_const(expr.children[1])
        and rational_const_value(expr.children[1]) == Fraction(1, 2)
    )
