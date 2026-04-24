from __future__ import annotations

from AST_nodes import Add, Const, Div, Expr, Mul, Var


ZERO = Const(0)
ONE = Const(1)


def is_zero(expr: Expr) -> bool:
    return isinstance(expr, Const) and expr.value == 0


def is_one(expr: Expr) -> bool:
    return isinstance(expr, Const) and expr.value == 1


def build_product(factors: list[Expr]) -> Expr:
    if len(factors) == 0:
        return ONE
    if len(factors) == 1:
        return factors[0]
    return Mul(factors)


def build_sum(terms: list[Expr]) -> Expr:
    if len(terms) == 0:
        return ZERO
    if len(terms) == 1:
        return terms[0]
    return Add(terms)


def build_div(numerator: Expr, denominator: Expr) -> Expr:
    if is_zero(numerator):
        return ZERO
    if is_one(denominator):
        return numerator
    return Div(numerator, denominator)


def rebuild_term(coefficient: Expr, basis: Expr) -> Expr:
    if is_zero(coefficient):
        return ZERO
    if is_one(basis):
        return coefficient
    if is_one(coefficient):
        return basis
    return Mul([coefficient, basis])


def split_term(term: Expr) -> tuple[Expr, Expr]:
    if term.is_const_expr():
        return term, ONE

    if isinstance(term, Mul):
        coefficient_factors: list[Expr] = []
        basis_factors: list[Expr] = []

        for factor in term.children:
            factor_coefficient, factor_basis = split_term(factor)
            if not is_one(factor_coefficient):
                coefficient_factors.append(factor_coefficient)
            if not is_one(factor_basis):
                basis_factors.append(factor_basis)

        return build_product(coefficient_factors), build_product(basis_factors)

    if isinstance(term, Div):
        numerator, denominator = term.children
        numerator_coefficient, numerator_basis = split_term(numerator)
        denominator_coefficient, denominator_basis = split_term(denominator)

        coefficient = build_div(numerator_coefficient, denominator_coefficient)
        basis = build_div(numerator_basis, denominator_basis)
        return coefficient, basis

    return ONE, term


def basis_key(expr: Expr):
    if isinstance(expr, Const):
        return ("Const", expr.value)
    if isinstance(expr, Var):
        return ("Var", expr.value)
    return (expr.type, tuple(basis_key(child) for child in expr.children))
