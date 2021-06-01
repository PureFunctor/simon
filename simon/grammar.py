from __future__ import annotations

import re
import typing as t

import attr


@attr.s(frozen=True, slots=True)
class Grammar:
    rules: dict[str, Rule] = attr.ib()
    terminals: dict[str, Terminal] = attr.ib()

    @classmethod
    def from_list(cls, rules: list[Rule], terminals: list[Terminal]) -> Grammar:
        _rules = {rule.name: rule for rule in rules}
        _terminals = {term.name: term for term in terminals}
        return cls(_rules, _terminals)

    def __getitem__(self, name: str) -> t.Union[Rule, Terminal]:
        if name.isupper():
            return self.terminals[name]
        else:
            return self.rules[name]


@attr.s(frozen=True, slots=True)
class Rule:
    name: str = attr.ib()
    rhs: Alts = attr.ib()

    def match(self, text: str, position: int, grammar: Grammar) -> t.Optional[Node]:
        if result := self.rhs.match(text, position, grammar):
            result.type_ = self.name
            return result
        return None


@attr.s(frozen=True, slots=True)
class Terminal:
    name: str = attr.ib()
    term: str = attr.ib()

    def match(self, text: str, position: int, grammar: Grammar) -> t.Optional[Node]:
        pattern = re.compile(re.escape(self.term))
        if result := pattern.match(text, position):
            return Node([result.group(0)], position, result.end(0))
        return None


class Expression:
    def match(self, text: str, position: int, grammar: Grammar) -> t.Optional[Node]:
        raise NotImplementedError


@attr.s(frozen=True)
class Literal(Expression):
    literal: str = attr.ib()

    def match(self, text: str, position: int, grammar: Grammar) -> t.Optional[Node]:
        pattern = re.compile(re.escape(self.literal))
        if result := pattern.match(text, position):
            return Node([result.group(0)], position, result.end(0))
        return None


@attr.s(frozen=True)
class RegEx(Expression):
    pattern: str = attr.ib()

    def match(self, text: str, position: int, grammar: Grammar) -> t.Optional[Node]:
        pattern = re.compile(self.pattern)
        if result := pattern.match(text, position):
            return Node([result.group(0)], position, result.end(0))
        return None


@attr.s(frozen=True)
class Name(Expression):
    name: str = attr.ib()

    def match(self, text: str, position: int, grammar: Grammar) -> t.Optional[Node]:
        matchable = grammar[self.name]
        if result := matchable.match(text, position, grammar):
            return result
        return None


@attr.s(frozen=True)
class Alts(Expression):
    alts: list[Expression] = attr.ib()

    def match(self, text: str, position: int, grammar: Grammar) -> t.Optional[Node]:
        for alt in self.alts:
            if result := alt.match(text, position, grammar):
                return result
        else:
            return None


@attr.s(frozen=True)
class Sequence(Expression):
    expressions: list[Expression] = attr.ib()

    def match(self, text: str, position: int, grammar: Grammar) -> t.Optional[Node]:
        results = []
        _position = position
        for expression in self.expressions:
            if result := expression.match(text, _position, grammar):
                results.append(result)
                _position = result.end
            else:
                return None
        else:
            return Node(results, position, _position)


_T = t.TypeVar("_T")


@attr.s(slots=True)
class Node(t.Generic[_T]):
    children: list[_T] = attr.ib()
    start: int = attr.ib()
    end: int = attr.ib()
    type_: str = attr.ib(default="")
