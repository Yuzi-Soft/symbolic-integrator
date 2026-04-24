from __future__ import annotations

from fractions import Fraction
import random

from AST_nodes import Add, Const, Cos, Div, Expr, Ln, Log, Mul, Pow, Sin, Var

function = {
    "pow(u, a)": 0.28,
    "pow(a, u)": 0.12,
    "sin(u)": 0.20,
    "cos(u)": 0.20,
    "log_a(u)": 0.07,
    "ln(u)": 0.13,
}

leaf = {
    "var": 0.45,
    "const": 0.55,
}

operation_root = {
    "leaf": 0.00,
    "add": 1.00,
    "sub": 0.00,
    "mul": 0.00,
    "div": 0.00,
    "cmp": 0.00,
}

operation_depth_two = {
    "leaf": 0.16,
    "add": 0.34,
    "sub": 0.06,
    "mul": 0.18,
    "div": 0.06,
    "cmp": 0.20,
}

operation = {
    "leaf": 0.18,
    "add": 0.24,
    "sub": 0.08,
    "mul": 0.20,
    "div": 0.08,
    "cmp": 0.22,
}


def number_split(N: int, n: int) -> list[int]:
    if N <= 0 or n <= 0:
        raise ValueError("N and n must be positive")
    if n > N:
        raise ValueError("N must be greater or equal to n")
    cuts = sorted(random.sample(range(1, N), n - 1))
    points = [0] + cuts + [N]
    return [points[i + 1] - points[i] for i in range(n)]


def random_select(domain: dict) -> str:
    if domain == {}:
        raise ValueError("domain must be non-empty")
    return random.choices(population=list(domain.keys()), weights=list(domain.values()), k=1)[0]


def select_operation(depth: int) -> str:
    if depth <= 0:
        raise ValueError("depth must be positive")
    if depth == 1:
        return random_select(operation_root)
    if depth == 2:
        return random_select(operation_depth_two)
    return random_select(operation)


def generate_expr(max_depth: int, cur_depth: int, nodes: int, context: Expr) -> Expr:
    if cur_depth >= max_depth or nodes <= 1:
        return generate_leaf(context)

    op = "leaf"
    for _ in range(8):
        candidate = select_operation(cur_depth)
        if _op_is_feasible(candidate, max_depth, cur_depth, nodes):
            op = candidate
            break

    if op == "leaf":
        expr = generate_leaf(context)
    elif op == "add":
        expr = generate_add(max_depth, cur_depth, nodes, context)
    elif op == "sub":
        expr = generate_sub(max_depth, cur_depth, nodes, context)
    elif op == "mul":
        expr = generate_mul(max_depth, cur_depth, nodes, context)
    elif op == "div":
        expr = generate_div(max_depth, cur_depth, nodes, context)
    else:
        expr = generate_cmp(max_depth, cur_depth, nodes, context)

    if expr.node_count() > nodes:
        return generate_leaf(context)
    return expr


def generate(max_depth: int = 4, nodes: int = 9) -> Expr:
    return generate_expr(max_depth=max_depth, cur_depth=1, nodes=nodes, context=Var("x"))


def generate_leaf(context: Expr) -> Expr:
    choice = random_select(leaf)
    if choice == "var":
        return Var("x")
    return random_const()


def generate_add(max_depth: int, cur_depth: int, nodes: int, context: Expr) -> Expr:
    terms = _generate_nary_children(max_depth, cur_depth, nodes, context)
    if len(terms) < 2:
        return generate_leaf(context)
    return Add(terms)


def generate_mul(max_depth: int, cur_depth: int, nodes: int, context: Expr) -> Expr:
    factors = _generate_nary_children(max_depth, cur_depth, nodes, context)
    if len(factors) < 2:
        return generate_leaf(context)
    return Mul(factors)


def generate_sub(max_depth: int, cur_depth: int, nodes: int, context: Expr) -> Expr:
    if nodes < 5 or cur_depth + 2 > max_depth:
        return generate_add(max_depth, cur_depth, nodes, context)

    left_nodes, right_nodes = number_split(nodes - 3, 2)
    left = generate_expr(max_depth, cur_depth + 1, left_nodes, context)
    right = generate_expr(max_depth, cur_depth + 2, right_nodes, context)
    return Add([left, Mul([Const(-1), right])])


def generate_div(max_depth: int, cur_depth: int, nodes: int, context: Expr) -> Expr:
    if nodes < 3:
        return generate_leaf(context)

    numerator_nodes, denominator_nodes = number_split(nodes - 1, 2)
    numerator = generate_expr(max_depth, cur_depth + 1, numerator_nodes, context)
    denominator = generate_expr(max_depth, cur_depth + 1, denominator_nodes, context)
    denominator = avoid_zero_const(denominator)
    return Div(numerator, denominator)


def generate_cmp(max_depth: int, cur_depth: int, nodes: int, context: Expr) -> Expr:
    chosen = select_function(nodes)

    if chosen == "sin(u)":
        child = generate_expr(max_depth, cur_depth + 1, nodes - 1, context)
        return Sin(child)

    if chosen == "cos(u)":
        child = generate_expr(max_depth, cur_depth + 1, nodes - 1, context)
        return Cos(child)

    if chosen == "ln(u)":
        child = generate_expr(max_depth, cur_depth + 1, nodes - 1, context)
        child = force_positive_const(child)
        return Ln(child)

    if chosen == "log_a(u)":
        base = random_const(positive=True, non_one=True)
        child = generate_expr(max_depth, cur_depth + 1, nodes - 2, context)
        child = force_positive_const(child)
        return Log(base, child)

    if chosen == "pow(u, a)":
        base = generate_expr(max_depth, cur_depth + 1, nodes - 2, context)
        exponent = random_const()
        return Pow(base, exponent)

    base = random_const(positive=True, non_zero=True, non_one=True)
    exponent = generate_expr(max_depth, cur_depth + 1, nodes - 2, context)
    return Pow(base, exponent)


def select_function(nodes: int) -> str:
    allowed: dict[str, float] = {}

    for name, weight in function.items():
        if weight <= 0:
            continue
        if name in ("sin(u)", "cos(u)", "ln(u)") and nodes >= 2:
            allowed[name] = weight
        if name in ("pow(u, a)", "pow(a, u)", "log_a(u)") and nodes >= 3:
            allowed[name] = weight

    if not allowed:
        return "sin(u)"
    return random_select(allowed)


def random_const(positive: bool = False, non_zero: bool = False, non_one: bool = False) -> Const:
    while True:
        kind = random.choices(population=["rational", "pi", "e"], weights=[0.78, 0.11, 0.11], k=1)[0]

        if kind == "rational":
            numerator = random.randint(1, 9) if positive else random.randint(-9, 9)
            denominator = random.randint(1, 5)
            candidate = Const(Fraction(numerator, denominator))
        elif kind == "pi":
            candidate = Const("pi")
        else:
            candidate = Const("e")

        if isinstance(candidate.value, Fraction):
            if positive and candidate.value <= 0:
                continue
            if non_zero and candidate.value == 0:
                continue
            if non_one and candidate.value == 1:
                continue

        return candidate


def avoid_zero_const(expr: Expr) -> Expr:
    if isinstance(expr, Const) and isinstance(expr.value, Fraction) and expr.value == 0:
        return Const(1)
    return expr


def force_positive_const(expr: Expr) -> Expr:
    if isinstance(expr, Const) and isinstance(expr.value, Fraction) and expr.value <= 0:
        return Const(2)
    return expr


def _generate_nary_children(max_depth: int, cur_depth: int, nodes: int, context: Expr) -> list[Expr]:
    if nodes < 3:
        return [generate_leaf(context)]

    max_arity = min(4, nodes - 1)
    if max_arity < 2:
        return [generate_leaf(context)]

    arity = random.randint(2, max_arity)
    node_split = number_split(nodes - 1, arity)
    return [generate_expr(max_depth, cur_depth + 1, count, context) for count in node_split]


def _op_is_feasible(op_name: str, max_depth: int, cur_depth: int, nodes: int) -> bool:
    if op_name == "leaf":
        return True
    if cur_depth >= max_depth:
        return False
    if op_name in ("add", "mul", "div"):
        return nodes >= 3
    if op_name == "cmp":
        return nodes >= 2
    if op_name == "sub":
        return nodes >= 5 and cur_depth + 2 <= max_depth
    return False
