from __future__ import annotations

import contextlib
from typing import Any, Callable, Collection, Generator, Tuple

import O365.utils.utils as utils
from maybe import Maybe

from .attribute import BaseAttribute, Attribute, FilterableAttribute, BooleanExpression, BooleanExpressionClause


class Query:
    def __init__(self, container: Any) -> None:
        self._container = container
        self._casing_function = self._container.protocol.casing_function
        self._query: utils.Query = None
        self._select: Tuple[BaseAttribute, ...] = None
        self._where: BooleanExpressionClause = None
        self._order: str = None
        self._limit: int = None

    def __call__(self) -> Any:
        return self.execute()

    @property
    def bulk(self) -> BulkAction:
        return BulkAction(self)

    def select(self, *args: Tuple[BaseAttribute, ...]) -> Query:
        self._select = args
        return self

    def where(self, *args: Any) -> Query:
        item, = args
        self._where = item._resolve()
        return self

    def order_by(self, order_clause: Any) -> Query:
        if isinstance(order_clause, str):
            self._order = order_clause
        elif isinstance(order_clause, Attribute) and issubclass(order_clause, FilterableAttribute):
            attribute = order_clause.asc()
            self._order = f"{self._casing_function(attribute.name)} {attribute.order_by}"
        elif isinstance(order_clause, FilterableAttribute):
            self._order = f"{self._casing_function(order_clause.name)} {order_clause.order_by}"
        else:
            raise TypeError(f"Unrecognized type '{type(order_clause)}' of '{order_clause}' for 'order_by'.")

        return self

    def limit(self, limit: int = 25) -> Query:
        self._limit = limit
        return self

    def execute(self) -> Any:
        self._query = utils.Query(protocol=self._container.protocol)
        self._build_select_clause()
        self._build_where_clause()

    def get_messages(self) -> list:
        return self.execute()

    def _build_select_clause(self) -> None:
        if self._select:
            self._query.select(*[self._casing_function(attribute.name) for attribute in self._select])

    def _build_where_clause(self) -> None:
        if self._where is not None:
            for expression, operator in self._where.expressions:
                self._build_clause_chunk(expression, operator)

    def _build_clause_chunk(self, expression: BooleanExpression, operator: utils.ChainOperator) -> None:
        if operator is not None:
            self._query = self._query.chain(operator.value)

        self._query = self._query.on_attribute(self._casing_function(expression.attr))

        with self._negation_context() if expression.negated else contextlib.nullcontext():
            self._query = expression.func(self._query, expression.arg)

    @contextlib.contextmanager
    def _negation_context(self) -> Generator[None, None, None]:
        self._query = self._query.negate()

        try:
            yield None
        finally:
            self.query = self._query.negate()


class BulkActionContext:
    def __init__(self, query: Query, action: Callable, args: Any = None, kwargs: Any = None) -> None:
        self._query, self._action, self._args, self._kwargs, self._committed = query, action, Maybe(args).else_(()), Maybe(kwargs).else_({}), False
        self.result: Collection = []

    def __len__(self) -> int:
        return len(self.result)

    def __bool__(self) -> bool:
        return len(self) > 0

    def commit(self) -> None:
        self._committed = True

    def execute(self) -> int:
        self._execute_query()
        self._perform_bulk_action()
        return len(self)

    def __enter__(self) -> BulkActionContext:
        self._execute_query()
        return self

    def __exit__(self, ex_type: Any, ex_value: Any, ex_traceback: Any) -> None:
        if self._committed:
            self._perform_bulk_action()

    def _execute_query(self) -> None:
        self.result = self._query.execute()

    def _perform_bulk_action(self) -> None:
        for msg in self.result:
            self._action(msg, *self._args, **self._kwargs)


class BulkAction:
    def __init__(self, query: Query) -> None:
        self._query = query
