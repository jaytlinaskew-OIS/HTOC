# -*- coding: utf-8 -*-

import re
from typing import Iterable, List

from ErrorCodes import ErrorCodes

# Optional import with a tiny fallback (AND/OR only)
try:
    from FilterOperator import FilterSetOperator  # type: ignore
except Exception:
    class _Op:
        def __init__(self, name): self.name = name
        def __repr__(self): return self.name
    class FilterSetOperator:  # type: ignore
        AND = _Op("AND")
        OR  = _Op("OR")


class FilterObject(object):
    """Holds query-time filters for read-only retrieval."""

    def __init__(self, tc_obj):
        self.tc = tc_obj
        self.tcl = self.tc.tcl  # logger

        self._api_filter_names: List[str] = []
        self._errors: List[str] = []
        self._filter_operator = FilterSetOperator.AND
        self._owners: List[str] = []
        self._post_filter_names: List[str] = []
        self._post_filters: List[object] = []
        self._resource_properties = None
        self._resource_type = None
        self._request_objects: List[object] = []

    # ---- builders ------------------------------------------------------------
    def _add_request_objects(self, data_obj) -> None:
        self._request_objects.append(data_obj)

    def add_owner(self, data) -> None:
        if isinstance(data, list):
            self._owners.extend(data)
        else:
            self._owners.append(data)

    def add_api_filter_name(self, data: str) -> None:
        self._api_filter_names.append(data)

    def add_filter_operator(self, data_enum) -> None:
        if data_enum not in (FilterSetOperator.AND, FilterSetOperator.OR):
            raise AttributeError(ErrorCodes.e1000.value.format(data_enum))
        self._filter_operator = data_enum

    def add_post_filter(self, data_obj) -> None:
        self._post_filters.append(data_obj)

    def add_post_filter_names(self, data: str) -> None:
        self._post_filter_names.append(data)

    # ---- properties ----------------------------------------------------------
    @property
    def operator(self):
        return self._filter_operator

    @property
    def post_filters(self) -> Iterable[object]:
        for obj in self._post_filters:
            yield obj

    @property
    def post_filters_len(self) -> int:
        return len(self._post_filters)

    @property
    def api_filter_names(self) -> List[str]:
        return sorted(self._api_filter_names)

    @property
    def filters(self) -> List[str]:
        """Return all 'add_*' filter method names (API + post)."""
        filters = []
        for name in sorted(self._api_filter_names):
            if name.startswith('add_'):
                filters.append(name)
        for name in sorted(self._post_filter_names):
            if name.startswith('add_'):
                filters.append(name)
        return filters

    @property
    def owners(self) -> List[str]:
        return self._owners

    @property
    def post_filter_names(self) -> List[str]:
        return sorted(self._post_filter_names)

    @property
    def resource_type(self):
        return self._resource_type

    # ---- iteration -----------------------------------------------------------
    def __iter__(self):
        for obj in self._request_objects:
            yield obj

    def __len__(self) -> int:
        return len(self._request_objects)

    def __str__(self) -> str:
        s = '\n{0:_^80}\n'.format('Filter Object')
        s += '{0:40}\n'.format('Filter Properties')
        s += '  {0:<29}{1:<50}\n'.format('Operator', self.operator)
        s += '  {0:<29}{1:<50}\n'.format('Request Objects', len(self._request_objects))

        if self._owners:
            s += '\n{0:40}\n'.format('Owners')
            for item in self._owners:
                s += '  {0:<29}{1:<50}\n'.format('Owner', item)

        if self._request_objects:
            s += '\n{0:40}\n'.format('Filters')
            for item in self._request_objects:
                desc = getattr(item, 'description', '')
                s += '  {0:<29}{1:<50}\n'.format('Filter', desc)

        if self._api_filter_names:
            s += '\n{0:40}\n'.format('API Filters')
            for item in self._api_filter_names:
                s += '  {0:<29}{1:<50}\n'.format('Filter', item)

        if self._post_filter_names:
            s += '\n{0:40}\n'.format('Post Filters')
            for item in self._post_filter_names:
                s += '  {0:<29}{1:<50}\n'.format('Filter', item)

        return s
