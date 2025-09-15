# -*- coding: utf-8 -*-

import time
from typing import Any, Dict, Iterable, List, Optional

import dateutil.parser
from ErrorCodes import ErrorCodes

# Optional: FilterOperator import with a small fallback
try:
    from Config.FilterOperator import FilterOperator  # type: ignore
except Exception:
    class _Op:
        def __init__(self, fn): self._fn = fn
        def __eq__(self, other): return self is other
        def value(self, a, b): return self._fn(a, b)
    class FilterOperator:  # type: ignore
        EQ  = _Op(lambda a, b: a == b)
        NE  = _Op(lambda a, b: a != b)
        LT  = _Op(lambda a, b: a <  b)
        LTE = _Op(lambda a, b: a <= b)
        GT  = _Op(lambda a, b: a >  b)
        GTE = _Op(lambda a, b: a >= b)


class Resource(object):
    """Read-only base container: filtering, indexing, retrieval, iteration."""

    def __init__(self, tc_obj):
        self.tc = tc_obj
        self.tcl = self.tc.tcl

        # filtered resource object list
        self._objects: List[Any] = []
        self._objects_dict: Dict[int, Any] = {}

        # master resource object list / indexes
        self._master_objects: List[Any] = []
        self._object_res_id_idx: Dict[Any, Any] = {}
        self._object_res_name_idx: Dict[str, List[Any]] = {}
        self._master_res_id_idx: Dict[Any, Any] = {}
        self._master_object_id_idx: Dict[int, Any] = {}

        # Post-filter indexes
        self._attribute_idx: Dict[str, List[Any]] = {}
        self._confidence_idx: Dict[int, List[Any]] = {}
        self._date_added_idx: Dict[int, List[Any]] = {}
        self._file_type_idx: Dict[str, List[Any]] = {}
        self._last_modified_idx: Dict[int, List[Any]] = {}
        self._name_idx: Dict[str, List[Any]] = {}
        self._rating_idx: Dict[float, List[Any]] = {}
        self._threat_assess_confidence_idx: Dict[float, List[Any]] = {}
        self._threat_assess_rating_idx: Dict[float, List[Any]] = {}
        self._tag_idx: Dict[str, List[Any]] = {}
        self._type_idx: Dict[str, List[Any]] = {}

        # misc defaults used by existing SDK patterns
        self._api_response: List[Any] = []
        self._current_filter = None
        self._error = False
        self._error_messages: List[str] = []
        self._filter_class = None
        self._filter_objects: List[Any] = []
        self._http_method = None
        self._id_mapping: Dict[Any, Any] = {}
        self._max_results: Optional[int] = None
        self._method = None
        self._object_class = None
        self._request_object = None
        self._resource_object = None
        self._resource_type = None
        self._result_count: int = 0
        self._status_code: List[int] = []
        self._uris: List[str] = []

    # ── Read helpers ──────────────────────────────────────────────────────────
    def add_obj(self, data_obj):
        """Add an already-retrieved object into filtered collections and indexes."""
        has_id = False

        if hasattr(data_obj, 'id'):
            resource_id = data_obj.id
            if resource_id is not None and resource_id not in self._object_res_id_idx:
                has_id = True
                self._object_res_id_idx.setdefault(resource_id, data_obj)
                self._objects.append(data_obj)
                self._objects_dict.setdefault(id(data_obj), data_obj)

        if hasattr(data_obj, 'name'):
            resource_name = data_obj.name
            if resource_name is not None:
                self._object_res_name_idx.setdefault(resource_name, []).append(data_obj)
                if not has_id:
                    self._objects.append(data_obj)

    def add_filter(self, resource_type=None):
        """Create and attach a filter object for retrieval."""
        if resource_type is not None:
            filter_obj = self._filter_class(self.tc, resource_type)
        else:
            filter_obj = self._filter_class(self.tc)
        self._filter_objects.append(filter_obj)
        return filter_obj

    def get_resource_by_identity(self, data):
        return self._master_object_id_idx.get(data)

    def add_master_resource_obj(self, data_obj, index):
        """Index a master object and build post-filter indexes."""
        resource_object_id = id(data_obj)
        duplicate = True

        self._master_object_id_idx.setdefault(resource_object_id, data_obj)

        if isinstance(index, dict):
            init = True
            for indx in index.values():
                if indx is None:
                    continue
                key = indx.upper()
                if key not in self._master_res_id_idx:
                    if init:
                        self._master_objects.append(data_obj)
                        init = False
                    self._master_res_id_idx[key] = data_obj
                    duplicate = False
                else:
                    resource_object_id = id(self._master_res_id_idx[key])
        else:
            if index not in self._master_res_id_idx:
                self._master_objects.append(data_obj)
                self._master_res_id_idx[index] = data_obj
                duplicate = False
            else:
                resource_object_id = id(self._master_res_id_idx[index])

        if not duplicate:
            if getattr(data_obj, 'confidence', None) is not None:
                self._confidence_idx.setdefault(data_obj.confidence, []).append(data_obj)

            if getattr(data_obj, 'date_added', None):
                dt = dateutil.parser.parse(data_obj.date_added)
                self._date_added_idx.setdefault(int(time.mktime(dt.timetuple())), []).append(data_obj)

            if getattr(data_obj, 'file_type', None):
                self._file_type_idx.setdefault(data_obj.file_type, []).append(data_obj)

            if getattr(data_obj, 'last_modified', None):
                dt = dateutil.parser.parse(data_obj.last_modified)
                self._last_modified_idx.setdefault(int(time.mktime(dt.timetuple())), []).append(data_obj)

            if getattr(data_obj, 'name', None):
                self._name_idx.setdefault(data_obj.name, []).append(data_obj)

            if getattr(data_obj, 'rating', None) is not None:
                self._rating_idx.setdefault(data_obj.rating, []).append(data_obj)

            if getattr(data_obj, 'threat_assess_confidence', None) is not None:
                self._threat_assess_confidence_idx.setdefault(data_obj.threat_assess_confidence, []).append(data_obj)

            if getattr(data_obj, 'threat_assess_rating', None) is not None:
                self._threat_assess_rating_idx.setdefault(data_obj.threat_assess_rating, []).append(data_obj)

            if getattr(data_obj, 'type', None):
                self._type_idx.setdefault(data_obj.type, []).append(data_obj)

            if getattr(data_obj, 'attributes', None):
                for attribute_obj in data_obj.attributes:
                    self._attribute_idx.setdefault(attribute_obj.type, []).append(data_obj)

            if getattr(data_obj, 'tags', None):
                for tag_obj in data_obj.tags:
                    self._tag_idx.setdefault(tag_obj.name, []).append(data_obj)

        return resource_object_id

    # ── Post Filters (read-only) ──────────────────────────────────────────────
    def filter_attribute(self, data, operator, description):
        if operator == FilterOperator.EQ:
            for obj in self._attribute_idx.get(data, []):
                obj.add_matched_filter(description); yield obj
        else:
            for key, objs in self._attribute_idx.items():
                if operator.value(key, data):
                    for obj in objs:
                        obj.add_matched_filter(description); yield obj

    def filter_confidence(self, data, operator, description):
        if operator == FilterOperator.EQ:
            for obj in self._confidence_idx.get(data, []):
                obj.add_matched_filter(description); yield obj
        else:
            for key, objs in self._confidence_idx.items():
                if operator.value(int(key), int(data)):
                    for obj in objs:
                        obj.add_matched_filter(description); yield obj

    def filter_date_added(self, data, operator, description):
        if operator == FilterOperator.EQ:
            for obj in self._date_added_idx.get(data, []):
                obj.add_matched_filter(description); yield obj
        else:
            for key, objs in self._date_added_idx.items():
                if operator.value(key, data):
                    for obj in objs:
                        obj.add_matched_filter(description); yield obj

    def filter_file_type(self, data, operator, description):
        if operator == FilterOperator.EQ:
            for obj in self._file_type_idx.get(data, []):
                obj.add_matched_filter(description); yield obj
        else:
            for key, objs in self._file_type_idx.items():
                if operator.value(key, data):
                    for obj in objs:
                        obj.add_matched_filter(description); yield obj

    def filter_last_modified(self, data, operator, description):
        if operator == FilterOperator.EQ:
            for obj in self._last_modified_idx.get(data, []):
                obj.add_matched_filter(description); yield obj
        else:
            for key, objs in self._last_modified_idx.items():
                if operator.value(key, data):
                    for obj in objs:
                        obj.add_matched_filter(description); yield obj

    def filter_name(self, data, operator, description):
        if operator == FilterOperator.EQ:
            for obj in self._name_idx.get(data, []):
                obj.add_matched_filter(description); yield obj

    def filter_rating(self, data, operator, description):
        if operator == FilterOperator.EQ:
            for obj in self._rating_idx.get(data, []):
                obj.add_matched_filter(description); yield obj
        else:
            for key, objs in self._rating_idx.items():
                if operator.value(float(key), float(data)):
                    for obj in objs:
                        obj.add_matched_filter(description); yield obj

    def filter_threat_assess_confidence(self, data, operator, description):
        if operator == FilterOperator.EQ:
            for obj in self._threat_assess_confidence_idx.get(data, []):
                obj.add_matched_filter(description); yield obj
        else:
            for key, objs in self._threat_assess_confidence_idx.items():
                if operator.value(float(key), float(data)):
                    for obj in objs:
                        obj.add_matched_filter(description); yield obj

    def filter_threat_assess_rating(self, data, operator, description):
        if operator == FilterOperator.EQ:
            for obj in self._threat_assess_rating_idx.get(data, []):
                obj.add_matched_filter(description); yield obj
        else:
            for key, objs in self._threat_assess_rating_idx.items():
                if operator.value(float(key), float(data)):
                    for obj in objs:
                        obj.add_matched_filter(description); yield obj

    def filter_tag(self, data, operator, description):
        self.tcl.debug('len tag index: {0}'.format(len(self._tag_idx)))
        if operator == FilterOperator.EQ:
            for obj in self._tag_idx.get(data, []):
                obj.add_matched_filter(description); yield obj
        else:
            for key, objs in self._tag_idx.items():
                if operator.value(key, data):
                    for obj in objs:
                        obj.add_matched_filter(description); yield obj

    def filter_type(self, data, operator, description):
        if operator == FilterOperator.EQ:
            for obj in self._type_idx.get(data, []):
                obj.add_matched_filter(description); yield obj
        else:
            for key, objs in self._type_idx.items():
                if operator.value(key, data):
                    for obj in objs:
                        obj.add_matched_filter(description); yield obj

    # ── Lookups & retrieval ───────────────────────────────────────────────────
    def get_resource_by_id(self, data):
        if data in self._master_res_id_idx:
            return self._method_wrapper(self._master_res_id_idx[data])
        elif isinstance(data, str) and data.upper() in self._master_res_id_idx:
            return self._method_wrapper(self._master_res_id_idx[data.upper()])
        else:
            self.tcl.warning(ErrorCodes.e10012.value.format(data))
            return None

    def get_resource_by_name(self, data):
        if data in self._master_res_id_idx:
            return self._method_wrapper(self._master_res_id_idx[data])
        else:
            self.tcl.warning(ErrorCodes.e10013.value.format(data))
            return None

    def retrieve(self):
        self.tc.api_filter_handler(self, self._filter_objects)
        del self._filter_objects[:]  # clear filters
        return self

    # ── Wrapper & iteration ───────────────────────────────────────────────────
    def _method_wrapper(self, obj):
        """Override in subclasses to wrap returned objects."""
        return obj  # identity in read-only mode

    def __getitem__(self, index):
        return self._method_wrapper(self._objects[index])

    def __iter__(self):
        for obj in self._objects:
            yield self._method_wrapper(obj)

    def __len__(self):
        return len(self._objects)
