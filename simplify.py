from __future__ import annotations
from fractions import Fraction
from AST_nodes import Expr, Const, Var, Add, Mul, Div, Pow, Sin, Cos, Ln, Log

def simplify(expr: Expr) -> Expr:


def simplify_once(expr: Expr) -> Expr:
    if(isinstance(expr, Add)):
        return simplify_add(expr)
        
        
def simplify_add(expr: Expr) -> Expr:
    children = expr.children
    simplified_children = []
    constant = Fraction(0)
    coef_pi = 0
    coef_e = 0
    for term in children:
        if isinstance(term, Const) and term.value == 0:
            continue
        if isinstance(term, Const) and term.value != 0:
            if term.is_e():
                coef_e += 1
            elif term.is_pi():
                coef_pi += 1
            else:
                assert isinstance(term.value, Fraction)
                constant += term.value
            continue
        if isinstance(term, Mul) and term.is_const_expr():
            if term.children[1]
            
        if isinstance(term, Add):
            for t in term.children:
                children.append(t)
            continue
        
        simplified_children.append(term)
        
    if(constant.numerator != 0):
        simplified_children.append(Const(constant))
    if(coef_pi != 0):
        simplified_children.append(Mul([Const(coef_pi), Const('pi')]))
    if(coef_e != 0):
        simplified_children.append(Mul([Const(coef_e), Const('e')]))

    if(len(simplified_children) == 0):
        return Const(0)
    if(len(simplified_children) == 1):
        return simplified_children[0]
    return Add(simplified_children)
