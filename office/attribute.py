from __future__ import annotations

from typing import Any, Callable, List, NoReturn, Optional, Tuple

import O365.utils.utils as utils
from subtypes import Enum


class BaseAttributeMeta(type):
    name: str

    def __eq__(self, other: Any) -> BooleanExpression:  # type: ignore
        return BooleanExpression(self.name, utils.Query.equals, other)

    def __ne__(self, other: Any) -> BooleanExpression:  # type: ignore
        return BooleanExpression(self.name, utils.Query.unequal, other)

    def __lt__(self, other: Any) -> BooleanExpression:
        return BooleanExpression(self.name, utils.Query.less, other)

    def __le__(self, other: Any) -> BooleanExpression:
        return BooleanExpression(self.name, utils.Query.less_equal, other)

    def __gt__(self, other: Any) -> BooleanExpression:
        return BooleanExpression(self.name, utils.Query.greater, other)

    def __ge__(self, other: Any) -> BooleanExpression:
        return BooleanExpression(self.name, utils.Query.greater_equal, other)

    def __and__(self, other: Any) -> BooleanExpressionClause:
        return self._resolve() & other._resolve()

    def __or__(self, other: Any) -> BooleanExpressionClause:
        return self._resolve() | other._resolve()

    def _resolve(self) -> Any:
        return BooleanExpression(self.name)._resolve()


class BooleanAttributeMeta(BaseAttributeMeta):
    def __invert__(self) -> BooleanExpression:
        return BooleanExpression(self.name, utils.Query.equals, True).negate()

    def _resolve(self) -> BooleanExpressionClause:
        return BooleanExpression(self.name, utils.Query.equals, True)._resolve()


class EnumerativeAttributeMeta(BaseAttributeMeta):
    def __new__(mcs, classname: str, bases: tuple, attributes: dict) -> Any:
        def make_function(func_name: str, value: str) -> Callable:
            def template(cls: EnumerativeAttributeMeta) -> BooleanExpression:
                return BooleanExpression(cls.name, utils.Query.equals, value)

            template.__name__ = func_name
            return template

        if attributes.get("enumeration") is not None:
            funcnames = [(f"is_{enum.name.lower()}", enum.value) for enum in attributes["enumeration"]]
            for name, val in funcnames:
                attributes[name] = classmethod(make_function(func_name=name, value=val))

        return type.__new__(mcs, classname, bases, attributes)


class NonFilterableMeta(type):
    def __getattr__(self, attr: str) -> NoReturn:
        raise AttributeError("This attribute cannot be used in the filter/where clause of a query.")


class BaseAttribute:
    name: str = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"


class NonFilterableAttribute(BaseAttribute, metaclass=NonFilterableMeta):
    pass


class FilterableAttribute(BaseAttribute):
    def __init__(self, order_by: str):
        self.order_by = order_by

    @classmethod
    def contains(cls, item: Any) -> BooleanExpression:
        return BooleanExpression(cls.name, utils.Query.contains, item)

    @classmethod
    def startswith(cls, text: str) -> BooleanExpression:
        return BooleanExpression(cls.name, utils.Query.startswith, text)

    @classmethod
    def endswith(cls, text: str) -> BooleanExpression:
        return BooleanExpression(cls.name, utils.Query.endswith, text)

    @classmethod
    def asc(cls) -> FilterableAttribute:
        return cls(Direction.ASCENDING)

    @classmethod
    def desc(cls) -> FilterableAttribute:
        return cls(Direction.DESCENDING)


class Attribute(FilterableAttribute, metaclass=BaseAttributeMeta):
    pass


class BooleanAttribute(FilterableAttribute, metaclass=BooleanAttributeMeta):
    pass


class EnumerativeAttribute(FilterableAttribute, metaclass=EnumerativeAttributeMeta):
    enumeration = None


class BooleanExpression:
    logical_opposites = {
        utils.Query.equals: utils.Query.unequal,
        utils.Query.unequal: utils.Query.equals,
        utils.Query.greater: utils.Query.less_equal,
        utils.Query.less_equal: utils.Query.greater,
        utils.Query.less: utils.Query.greater_equal,
        utils.Query.greater_equal: utils.Query.less,
    }

    def __init__(self, attribute_name: str, query_func: Callable = None, argument: Any = None) -> None:
        self.func, self.attr, self.arg, self.negated = query_func, attribute_name, argument, False

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"

    def __and__(self, other: Any) -> BooleanExpressionClause:
        return self._resolve() & other._resolve()

    def __or__(self, other: Any) -> BooleanExpressionClause:
        return self._resolve() | other._resolve()

    def __invert__(self) -> BooleanExpression:
        return self.negate()

    def negate(self) -> BooleanExpression:
        if self.func in self.logical_opposites:
            self.func = self.logical_opposites[self.func]
        else:
            self.negated = not self.negated

        return self

    def _resolve(self) -> BooleanExpressionClause:
        return BooleanExpressionClause(self)


class BooleanExpressionClause:
    def __init__(self, expression: BooleanExpression) -> None:
        self.expressions: List[Tuple[BooleanExpression, Optional[utils.ChainOperator]]] = [(expression, None)]

    def __and__(self, other: Any) -> BooleanExpressionClause:
        return self._coalesce(other._resolve(), utils.ChainOperator.AND)

    def __or__(self, other: Any) -> BooleanExpressionClause:
        return self._coalesce(other._resolve(), utils.ChainOperator.OR)

    def _coalesce(self, clause: BooleanExpressionClause, operator: utils.ChainOperator) -> BooleanExpressionClause:
        clause.expressions[0] = (clause.expressions[0][0], operator)
        self.expressions.extend(clause.expressions)
        return self

    def _resolve(self) -> BooleanExpressionClause:
        return self


class Direction(Enum):
    ASCENDING, DESCENDING = "asc", "desc"
