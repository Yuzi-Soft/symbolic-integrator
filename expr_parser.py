from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from AST_nodes import Add, Const, Cos, Div, Expr, Ln, Log, Mul, Pow, Sin, Var


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    position: int


def parse_expr(text: str) -> Expr:
    parser = _Parser(_tokenize(text))
    expr = parser.parse_expression()
    parser.expect("EOF")
    return expr


def _tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    index = 0

    while index < len(text):
        ch = text[index]

        if ch.isspace():
            index += 1
            continue

        if text.startswith("Log_", index):
            tokens.append(Token("LOG", "Log_", index))
            index += 4
            continue
        if text.startswith("Sin", index):
            tokens.append(Token("FUNC", "Sin", index))
            index += 3
            continue
        if text.startswith("Cos", index):
            tokens.append(Token("FUNC", "Cos", index))
            index += 3
            continue
        if text.startswith("Ln", index):
            tokens.append(Token("FUNC", "Ln", index))
            index += 2
            continue
        if text.startswith("pi", index):
            tokens.append(Token("SYMBOL", "pi", index))
            index += 2
            continue
        if ch in "()+-*/^":
            tokens.append(Token(ch, ch, index))
            index += 1
            continue
        if ch.isdigit():
            start = index
            while index < len(text) and text[index].isdigit():
                index += 1
            if index < len(text) and text[index] == "/" and index + 1 < len(text) and text[index + 1].isdigit():
                index += 1
                while index < len(text) and text[index].isdigit():
                    index += 1
            tokens.append(Token("NUMBER", text[start:index], start))
            continue
        if ch == "x" or ch == "e":
            tokens.append(Token("SYMBOL", ch, index))
            index += 1
            continue

        raise ValueError(f"Unexpected character {ch!r} at position {index}")

    tokens.append(Token("EOF", "", len(text)))
    return tokens


class _Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.index = 0

    def parse_expression(self) -> Expr:
        return self.parse_add()

    def parse_add(self) -> Expr:
        terms = [self.parse_mul()]

        while self.match("+") or self.match("-"):
            operator = self.previous().kind
            term = self.parse_mul()
            if operator == "-":
                term = _negate(term)
            terms.append(term)

        if len(terms) == 1:
            return terms[0]
        return Add(terms)

    def parse_mul(self) -> Expr:
        expr = self.parse_pow()

        while self.match("*") or self.match("/"):
            operator = self.previous().kind
            right = self.parse_pow()
            if operator == "*":
                if isinstance(expr, Mul):
                    expr = Mul(expr.children + [right])
                else:
                    expr = Mul([expr, right])
            else:
                expr = Div(expr, right)

        return expr

    def parse_pow(self) -> Expr:
        expr = self.parse_unary()

        if self.match("^"):
            exponent = self.parse_pow()
            expr = Pow(expr, exponent)

        return expr

    def parse_unary(self) -> Expr:
        if self.match("+"):
            return self.parse_unary()
        if self.match("-"):
            return _negate(self.parse_unary())
        return self.parse_primary()

    def parse_primary(self) -> Expr:
        if self.match("NUMBER"):
            return _const_from_number(self.previous().value)

        if self.match("SYMBOL"):
            value = self.previous().value
            if value == "x":
                return Var("x")
            return Const(value)

        if self.match("FUNC"):
            name = self.previous().value
            self.expect("(")
            child = self.parse_expression()
            self.expect(")")
            if name == "Sin":
                return Sin(child)
            if name == "Cos":
                return Cos(child)
            if name == "Ln":
                return Ln(child)
            raise ValueError(f"Unsupported function {name!r}")

        if self.match("LOG"):
            base = self.parse_log_base()
            self.expect("(")
            argument = self.parse_expression()
            self.expect(")")
            return Log(base, argument)

        if self.match("("):
            expr = self.parse_expression()
            self.expect(")")
            return expr

        token = self.peek()
        raise ValueError(f"Unexpected token {token.kind!r} at position {token.position}")

    def parse_log_base(self) -> Const:
        if self.match("NUMBER"):
            return _const_from_number(self.previous().value)
        if self.match("SYMBOL"):
            value = self.previous().value
            if value in ("e", "pi"):
                return Const(value)
            raise ValueError(f"Invalid log base symbol {value!r} at position {self.previous().position}")

        token = self.peek()
        raise ValueError(f"Expected log base at position {token.position}")

    def match(self, kind: str) -> bool:
        if self.peek().kind != kind:
            return False
        self.index += 1
        return True

    def expect(self, kind: str) -> Token:
        token = self.peek()
        if token.kind != kind:
            raise ValueError(f"Expected {kind!r} at position {token.position}, got {token.kind!r}")
        self.index += 1
        return token

    def peek(self) -> Token:
        return self.tokens[self.index]

    def previous(self) -> Token:
        return self.tokens[self.index - 1]


def _const_from_number(text: str) -> Const:
    if "/" in text:
        numerator, denominator = text.split("/", 1)
        return Const(Fraction(int(numerator), int(denominator)))
    return Const(int(text))


def _negate(expr: Expr) -> Expr:
    if isinstance(expr, Const) and isinstance(expr.value, Fraction):
        return Const(-expr.value)
    return Mul([Const(-1), expr])
