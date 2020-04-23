from __future__ import annotations

import contextlib
from typing import Any, Callable, Collection, Generator, Tuple, Union, Optional

import O365.utils.utils as utils

from maybe import Maybe
from miscutils import issubclass_safe

from .attribute import BaseAttribute, Attribute, BooleanAttributeMeta, FilterableAttribute, BooleanExpression, BooleanExpressionClause


class Query:
    """A class for querying the api elements within a given collection."""

    def __init__(self, container: Any) -> None:
        self._container = container
        self._casing_function = self._container.protocol.casing_function
        self._query = utils.Query(protocol=self._container.protocol)
        self._select: Optional[Tuple[BaseAttribute, ...]] = None
        self._where: Optional[BooleanExpressionClause] = None
        self._order: Optional[FilterableAttribute] = None
        self._limit: Optional[int] = None

    def __repr__(self) -> str:
        return repr(self._query)

    def __call__(self) -> Any:
        return self.execute()

    @property
    def bulk(self) -> BulkAction:
        """Perform a bulk action on the resultset of this query."""
        return BulkAction(self)

    def select(self, *args: Tuple[BaseAttribute, ...]) -> Query:
        """Set the attributes that will be queried. If this method is not called, all message attributes will be returned."""
        self._query._selects = set()
        self._select = args
        self._build_select_clause()
        return self

    def where(self, resolvable_element: Union[Attribute, BooleanExpression, BooleanExpressionClause]) -> Query:
        """Set the filter clause on this query. Accepts a single boolean attribute, boolean expression or boolean expression clause."""
        self._query.clear_filters()
        self._where = resolvable_element._resolve()
        self._build_where_clause()
        return self

    def order_by(self, order_clause: Any) -> Query:
        """Set the filter clause on this query. Accepts a single boolean attribute, boolean expression or boolean expression clause."""
        self._query.clear_order()
        self._order = order_clause
        self._build_order_by_clause()
        return self

    def limit(self, limit: int = 25) -> Query:
        """Set the limit on the number of objects that may be returned."""
        self._limit = limit
        return self

    def execute(self) -> Any:
        """Execute this query and return the results."""
        raise NotImplementedError

    def _build_select_clause(self) -> None:
        if self._select:
            self._query.select(*[self._casing_function(attribute.name) for attribute in self._select])

    def _build_where_clause(self) -> None:
        if self._where is not None:
            if isinstance(self._where, BooleanExpression):
                self._build_boolean_expression(self._where)
            elif isinstance(self._where, BooleanExpressionClause):
                self._build_boolean_expression_clause(self._where)
            else:
                raise TypeError(f"Argument to filter clause of '{type(self).__name__}' must be '{type(BooleanExpression.__name__)}' or '{type(BooleanExpressionClause.__name__)}', not '{type(self._where).__name__}'.")

    def _build_order_by_clause(self) -> None:
        if isinstance(self._order, str):
            self._query.order_by(self._order)
        elif isinstance(self._order, FilterableAttribute):
            self._query.order_by(self._casing_function(self._order.name), ascending=self._order.ascending)
        elif issubclass_safe(self._order, FilterableAttribute):
            attribute = self._order.asc()
            self._query.order_by(self._casing_function(attribute.name), ascending=self._order.ascending)
        else:
            raise TypeError(f"Unrecognized type '{type(self._order)}' of '{self._order}' for 'order_by'.")

    def _build_boolean_expression_clause(self, clause: BooleanExpressionClause) -> None:
        with self._precedence_grouping():
            self._build_side(clause.left)
            self._build_chain_operator(clause.operator)
            self._build_side(clause.right)

    def _build_side(self, side: Union[BooleanExpression, BooleanExpressionClause]) -> None:
        if isinstance(side, BooleanAttributeMeta):
            side = side._resolve()

        if isinstance(side, BooleanExpression):
            self._build_boolean_expression(side)
        elif isinstance(side, BooleanExpressionClause):
            self._build_boolean_expression_clause(side)
        else:
            raise TypeError(f"The sides of '{type(BooleanExpressionClause).__name__}' must be '{type(BooleanExpression).__name__}' or '{type(BooleanExpressionClause).__name__}', not '{type(side).__name__}'.")

    def _build_chain_operator(self, operator: utils.ChainOperator) -> None:
        self._query.chain(operator.value)

    def _build_boolean_expression(self, expression: BooleanExpression) -> None:
        self._query.on_attribute(self._casing_function(expression.attr))
        with self._negation() if expression.negated else contextlib.nullcontext():
            expression.func(self._query, expression.arg)

    @contextlib.contextmanager
    def _negation(self) -> Generator[None, None, None]:
        self._query.negate()
        yield
        self._query.negate()

    @contextlib.contextmanager
    def _precedence_grouping(self) -> Generator[None, None, None]:
        self._query.open_group()
        yield
        self._query.close_group()


class BulkActionContext:
    """A class representing the context within which a bulk action is performed. It can be used as a context manager and will automatically perform the action upon dropping out of scope if the action was committed."""

    def __init__(self, query: Query, action: Callable, args: Any = None, kwargs: Any = None) -> None:
        self._query, self._action, self._args, self._kwargs, self._committed = query, action, Maybe(args).else_(()), Maybe(kwargs).else_({}), False
        self.result: Collection = []

    def __len__(self) -> int:
        return len(self.result)

    def __bool__(self) -> bool:
        return len(self) > 0

    def __enter__(self) -> BulkActionContext:
        self._execute_query()
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        if self._committed:
            self._perform_bulk_action()

    def commit(self) -> None:
        """Commit the action corresponding to this context. It will be performed when this object drops out of context."""
        self._committed = True

    def execute(self) -> int:
        """Perform the bulk action corresponding to this context."""
        self._execute_query()
        self._perform_bulk_action()
        return len(self)

    def _execute_query(self) -> None:
        self.result = self._query.execute()

    def _perform_bulk_action(self) -> None:
        for msg in self.result:
            self._action(msg, *self._args, **self._kwargs)


class BulkAction:
    """A class representing a bulk action performed on the resultset of a query."""

    def __init__(self, query: Query) -> None:
        self._query = query
