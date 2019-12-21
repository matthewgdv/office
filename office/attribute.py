from __future__ import annotations

from typing import Any, Callable, NoReturn, Union

import O365.utils.utils as utils
from subtypes import ValueEnum

# TODO: Add all attributes from https://docs.microsoft.com/en-us/previous-versions/office/office-365-api/api/version-2.0/complex-types-for-mail-contacts-calendar#Filter


class Direction(ValueEnum):
    """An Enum of the directions an 'order_by' clause can go in."""

    ASCENDING, DESCENDING = "asc", "desc"


class BaseAttributeMeta(type):
    """The metaclass shared by all attributes, implementing operator functionality."""

    name: str

    def __hash__(self) -> int:
        return id(self)

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
        raise ValueError(f"Cannot resolve an object of type '{self.__name__}' without using it as part of a boolean expression.")


class BooleanAttributeMeta(BaseAttributeMeta):
    """A metaclass for boolean attributes which allows them to be automatically resolved to a True boolean expression, or inverted ('~' operator) for a False one."""

    def __invert__(self) -> BooleanExpression:
        return BooleanExpression(self.name, utils.Query.equals, False)

    def _resolve(self) -> BooleanExpression:
        return BooleanExpression(self.name, utils.Query.equals, True)


class EnumerativeAttributeMeta(BaseAttributeMeta):
    """A metaclass for enumerative attributes which dynamically creates methods that resolve them to a boolean expression based on an enumeration."""

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
    """A metaclass for attributes which cannot be used in the filter clause of a query and will raise errors when attempting to do so."""

    def __getattr__(self, attr: str) -> NoReturn:
        raise AttributeError("This attribute cannot be used in the filter/where clause of a query.")


class BaseAttribute:
    """An abstract base class for all attributes to inherit from, providing basic functionality."""

    name: str = None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"


class NonFilterableAttribute(BaseAttribute, metaclass=NonFilterableMeta):
    """A class for attributes to inherit from which cannot be used in the filter clause of a query."""


class FilterableAttribute(BaseAttribute):
    """An abstract base class for concrete attribute classes to inherit from which can be used in the filter clause of a query."""

    def __init__(self, order_by: Direction):
        self.order_by, self.ascending = order_by, order_by == Direction.ASCENDING

    @classmethod
    def contains(cls, item: str) -> BooleanExpression:
        """Return a boolean expression indicating whether this attribute contains the given value."""
        return BooleanExpression(cls.name, utils.Query.contains, item)

    @classmethod
    def startswith(cls, text: str) -> BooleanExpression:
        """Return a boolean expression indicating whether this attribute starts with the given value."""
        return BooleanExpression(cls.name, utils.Query.startswith, text)

    @classmethod
    def endswith(cls, text: str) -> BooleanExpression:
        """Return a boolean expression indicating whether this attribute ends with the given value."""
        return BooleanExpression(cls.name, utils.Query.endswith, text)

    @classmethod
    def asc(cls) -> FilterableAttribute:
        """Create a direction-aware instance of this attribute that can be provided to 'order_by' clauses."""
        return cls(Direction.ASCENDING)

    @classmethod
    def desc(cls) -> FilterableAttribute:
        """Create a direction-aware instance of this attribute that can be provided to 'order_by' clauses."""
        return cls(Direction.DESCENDING)


class Attribute(FilterableAttribute, metaclass=BaseAttributeMeta):
    """A class for ordinary attributes to inherit from."""


class BooleanAttribute(FilterableAttribute, metaclass=BooleanAttributeMeta):
    """A class for boolean attributes to inherit from."""


class EnumerativeAttribute(FilterableAttribute, metaclass=EnumerativeAttributeMeta):
    """A class for attributes to inherit from which always compare their value against a finite set of strings."""

    enumeration = None


class BaseExpressionElement:
    """An abstract base class for expression element such as boolean expressions and clauses to inherit from."""

    negated: bool

    def __repr__(self) -> str:
        return f"{type(self).__name__}({', '.join([f'{attr}={repr(val)}' for attr, val in self.__dict__.items() if not attr.startswith('_')])})"

    def __and__(self, other: Union[BooleanExpression, BooleanExpressionClause]) -> BooleanExpressionClause:
        return BooleanExpressionClause(left=self, operator=utils.ChainOperator.AND, right=other)

    def __or__(self, other: Union[BooleanExpression, BooleanExpressionClause]) -> BooleanExpressionClause:
        return BooleanExpressionClause(left=self, operator=utils.ChainOperator.OR, right=other)

    def _resolve(self) -> BaseExpressionElement:
        return self


class BooleanExpression(BaseExpressionElement):
    """A class representing a query expression that evaluates to a boolean by comparing an attribute against a value using a given operator."""

    logical_opposites = {
        utils.Query.equals: utils.Query.unequal,
        utils.Query.unequal: utils.Query.equals,
        utils.Query.greater: utils.Query.less_equal,
        utils.Query.less_equal: utils.Query.greater,
        utils.Query.less: utils.Query.greater_equal,
        utils.Query.greater_equal: utils.Query.less,
    }

    def __init__(self, attribute_name: str, query_func: Callable = None, argument: Any = None) -> None:
        self.attr, self.func, self.arg, self.negated = attribute_name, query_func, argument, False

    def __invert__(self) -> BooleanExpression:
        return self.negate()

    def negate(self) -> BooleanExpression:
        """Negate this boolean expression by either using the logically oposite operator, or, if none exists, using the 'not' logical operator."""
        if self.func in self.logical_opposites:
            self.func = self.logical_opposites[self.func]
        else:
            self.negated = not self.negated

        return self


class BooleanExpressionClause(BaseExpressionElement):
    """A class representing a binary clause of where each side contains either a boolean expression or another clause."""

    def __init__(self, left: BaseExpressionElement, operator: utils.ChainOperator, right: Union[BooleanExpression, BooleanExpressionClause]) -> None:
        self.left, self.operator, self.right = left, operator, right
