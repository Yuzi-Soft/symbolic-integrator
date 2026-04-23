from __future__ import annotations
from fractions import Fraction
from AST_nodes import Expr, Const, Var, Add, Mul, Div, Pow, Sin, Cos, Ln, Log

def differentiate(expr: Expr) -> Expr:
    if isinstance(expr, Const) or expr.is_const_expr():
        return Const(0)
    
    if isinstance(expr, Var):
        return Const(1)
    
    if isinstance(expr, Add):
        return Add([differentiate(term) for term in expr.children])
    
    if isinstance(expr, Mul):
        return diff_multiplication(expr)
    
    if isinstance(expr, Div):
        return diff_division(expr)
    
    if isinstance(expr, Pow):
        return diff_pow(expr)
    
    if isinstance(expr, Sin):
        return Mul([Cos(expr.children[0]), differentiate(expr.children[0]) ])
    
    if isinstance(expr, Cos):
        return Mul([Const(-1), Sin(expr.children[0]), differentiate(expr.children[0]) ])
    
    if isinstance(expr, Ln):
        return Div(differentiate(expr.children[0]), expr.children[0] )
    
    if isinstance(expr, Log):
        return Div(differentiate(expr.children[1]), Mul([expr.children[1], Ln(expr.children[0])]))
    
    raise NotImplementedError(f"Unsupported node: {type(expr).__name__}")

def diff_multiplication(expr: Expr) -> Expr:
    terms = []
    for i, it in enumerate(expr.children):
        diff_term = [differentiate(term) if j==i else term for j, term in enumerate(expr.children)]
        terms.append(Mul(diff_term))
    return Add(terms)

def diff_division(expr: Expr) -> Expr:
    num = expr.children[0]
    den = expr.children[1]
    dnum = differentiate(num)
    dden = differentiate(den)
    numerator = Add( [Mul([dnum, den]), Mul([Const(-1), num, dden])] )
    denominator = Pow(den, Const(2))
    return Div(numerator, denominator)

def diff_pow(expr: Expr) -> Expr:
    base = expr.children[0]
    power = expr.children[1]
    
    if(power.is_const_expr()):
        if isinstance(power, Const):
            if(power == Const(0)):
                return Const(0)
            if(power == Const(1)):
                return differentiate(base)
            return Mul([power, Pow(base, Add([power, Const(-1)])), differentiate(base)])
        return  Mul([power, Pow(base, Add([power, Const(-1)])), differentiate(base)])
    
    if(base.is_const_expr()):
        return Mul([Pow(base, power), Ln(base), differentiate(power)])
    
    raise NotImplementedError("Pow with variable base and variable exponent is unsupported")