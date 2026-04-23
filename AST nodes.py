from __future__ import annotations
from abc import ABC, abstractmethod
from fractions import Fraction

class Expr(ABC):

    @property
    @abstractmethod
    def type(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def children(self) -> list:
        raise NotImplementedError

    @abstractmethod
    def pretty(self) -> str:
        raise NotImplementedError

    def depth(self) -> int:
        if not self.children:
            return 1
        return 1 + max(child.depth() for child in self.children)

    def node_count(self) -> int:
        return 1 + sum(child.node_count() for child in self.children)

    def validate(self) -> None:
        if not isinstance(self.type, str) or not self.type:
            raise TypeError("Expr.type must be a non-empty str")
        if not isinstance(self.children, list):
            raise TypeError("Expr.children must be list")
        for index, child in enumerate(self.children):
            if not isinstance(child, Expr):
                raise TypeError(f"children[{index}] must be Expr, got {type(child)!r}")

    def is_const_expr(self) -> bool:
        if self.type == "Var":
            return False
        if self.type == "Const":
            return True
        return all(child.is_const_expr() for child in self.children)

    def is_var_expr(self) -> bool:
        return not self.is_const_expr()

class Const(Expr):
    @property
    def type(self) -> str:
        return "Const"

    @property
    def children(self) -> list:
        return []
    
    def __init__(self, val):
        if type(val) is not Fraction:
            raise TypeError(f"Const.value must be Fraction, got {type(val).__name__}")
        self.value = val
        self.validate()
        
    def pretty(self) -> str:
        return str(self.value)
    
class Var(Expr):
    @property
    def type(self) -> str:
        return "Var"

    @property
    def children(self) -> list:
        return []
    
    def __init__(self, val):
        if not val == "x":
            raise TypeError(f"Var.value must be \"x\", got {type(val).__name__}")
        self.value = val
        self.validate()
        
    def pretty(self) -> str:
        return str(self.value)

class Add(Expr):
    @property
    def type(self) -> str:
        return "Add"

    @property
    def children(self) -> list:
        return list(self._children)
    
    def __init__(self, lst):
        if not isinstance(lst, list):
            raise TypeError(f"Add.lst must be list, got {type(lst).__name__}")
        if len(lst) < 2:
            raise ValueError("Add requires at least 2 Expr terms")
        self._children = []
        for index, expr in enumerate(lst):
            if not isinstance(expr, Expr):
                raise TypeError(f"Add.lst[{index}] must be Expr, got {type(expr).__name__}")
            self._children.append(expr)
        self.validate()
        
        
        
    def pretty(self) -> str:
        return "(" + " + ".join(expr.pretty() for expr in self._children) + ")"
    
class Mul(Expr):
    @property
    def type(self) -> str:
        return "Mul"

    @property
    def children(self) -> list:
        return list(self._children)
    
    def __init__(self, lst):
        if not isinstance(lst, list):
            raise TypeError(f"Mul.lst must be list, got {type(lst).__name__}")
        if len(lst) < 2:
            raise ValueError("Mul requires at least 2 Expr terms")
        self._children = []
        for index, expr in enumerate(lst):
            if not isinstance(expr, Expr):
                raise TypeError(f"Mul.lst[{index}] must be Expr, got {type(expr).__name__}")
            self._children.append(expr)
        self.validate()
        
        
        
    def pretty(self) -> str:
        return "(" + " * ".join(expr.pretty() for expr in self._children) + ")"
    
class Div(Expr):
    @property
    def type(self) -> str:
        return "Div"

    @property
    def children(self) -> list:
        return list(self._children)
    
    def __init__(self, numerator, denominator):
        if not isinstance(numerator, Expr):
            raise TypeError(f"Div.numerator must be list/tuple[Expr], got {type(numerator).__name__}")
        if not isinstance(denominator, Expr):
            raise TypeError(f"Div.denominator must be list/tuple[Expr], got {type(denominator).__name__}")
        
        self._children = []
        self._children.append(numerator)
        self._children.append(denominator)
        self.validate()
        
    def pretty(self) -> str:
        return "(" + self._children[0].pretty() + " / " + self._children[1].pretty() + ")"
    
class Pow(Expr):
    @property
    def type(self) -> str:
        return "Pow"

    @property
    def children(self) -> list:
        return list(self._children)
    
    def __init__(self, expr, pow):
        if not isinstance(expr, Expr):
            raise TypeError(f"Pow.expr must be Expr, got {type(expr).__name__}")
        if not isinstance(pow, Expr):
            raise TypeError(f"Pow.pow must be Expr, got {type(pow).__name__}")
        self._children = []
        self._children.append(expr)
        self._children.append(pow)
        self.validate()
        
    def pretty(self) -> str:
        return "(" + self._children[0].pretty() + " ^ " + self._children[1].pretty() + ")"
    
class Cos(Expr):
    @property
    def type(self) -> str:
        return "Cos"

    @property
    def children(self) -> list:
        return list(self._children)
    
    def __init__(self, expr):
        if not isinstance(expr, Expr):
            raise TypeError(f"Cos.expr must be list, got {type(expr).__name__}")
        self._children = []
        self._children.append(expr)
        self.validate()
        
    def pretty(self) -> str:
        return "Cos(" + self._children[0].pretty()+ ")"
    
class Sin(Expr):
    @property
    def type(self) -> str:
        return "Sin"

    @property
    def children(self) -> list:
        return list(self._children)
    
    def __init__(self, expr):
        if not isinstance(expr, Expr):
            raise TypeError(f"Sin.expr must be list, got {type(expr).__name__}")
        self._children = []
        self._children.append(expr)
        self.validate()
        
    def pretty(self) -> str:
        return "Sin(" + self._children[0].pretty()+ ")"
    
class Log(Expr):
    @property
    def type(self) -> str:
        return "Log"

    @property
    def children(self) -> list:
        return list(self._children)
    
    def __init__(self, base, expr):
        if not isinstance(expr, Expr):
            raise TypeError(f"Log.expr must be list, got {type(expr).__name__}")
        if not isinstance(base, Const):
            raise TypeError(f"Log.base must be list, got {type(base).__name__}")
        if base.value <= 0 or base.value == 1:
            raise TypeError(f"Log.base must be positve and cannot be 1, got {type(base).__name__}")
        self._children = []
        self._children.append(base)
        self._children.append(expr)
        self.base = base
        self.validate()
        
    def pretty(self) -> str:
        return "Log_" + self._children[0].pretty() + "(" + self._children[1].pretty()+ ")"
    
