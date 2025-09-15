# -*- coding: utf-8 -*-

import types
from typing import Any, Dict, Iterable, List, Optional

from FilterObject import FilterObject
from RequestObject import RequestObject
from Resource import Resource

# Optional parsers (safe if absent)
try:
    from threatconnect.OwnerMetricsObject import parse_metrics  # type: ignore
except Exception:
    parse_metrics = None
try:
    from threatconnect.OwnerMembersObject import parse_member  # type: ignore
except Exception:
    parse_member = None

# Minimal, built-in endpoint map (no ApiProperties needed)
_OWNERS_PROPS: Dict[str, Dict[str, Any]] = {
    "base":    {"owner_allowed": False, "uri": "/v2/owners",         "pagination": True},
    "mine":    {"owner_allowed": False, "uri": "/v2/owners/mine",    "pagination": True},
    "members": {"owner_allowed": False, "uri": "/v2/owners/members", "pagination": True},
    "metrics": {"owner_allowed": False, "uri": "/v2/owners/metrics", "pagination": True},
}

class Owners(Resource):
    """Read-only Owners resource (no ApiProperties/ResourceType)."""

    def __init__(self, tc_obj):
        super().__init__(tc_obj)
        self._filter_class = OwnerFilterObject

    def _method_wrapper(self, resource_object):
        # Read-only path: just return the raw/simple object
        return resource_object

    @property
    def _props(self) -> Dict[str, Any]:
        return _OWNERS_PROPS

    def _make_request(self, key: str, *, description: Optional[str] = None) -> RequestObject:
        p = self._props[key]
        ro = RequestObject()
        if description:
            ro.set_description(description)
        ro.set_http_method("GET")                # force GET (read-only)
        ro.set_owner_allowed(p["owner_allowed"])
        ro.set_request_uri(p["uri"])
        ro.set_resource_pagination(p["pagination"])
        return ro

    def _fetch_json(self, ro: RequestObject) -> Optional[Dict[str, Any]]:
        resp = self.tc.api_request(ro)
        if resp.headers.get("content-type") == "application/json":
            data = resp.json()
            if data.get("status") == "Success":
                return data
        return None

    @property
    def default_request_object(self) -> RequestObject:
        return self._make_request("base")

    def get_owner_by_id(self, owner_id: int):
        if not isinstance(owner_id, int):
            return None
        return next((o for o in self._objects if getattr(o, "id", None) == owner_id), None)

    def get_owner_by_name(self, name: str):
        if not isinstance(name, str):
            return None
        return next((o for o in self._objects if getattr(o, "name", None) == name), None)

    @property
    def names(self) -> Iterable[str]:
        for obj in self._objects:
            yield getattr(obj, "name", "")

    def retrieve_metrics(self) -> List[Any]:
        ro = self._make_request("metrics", description="load global metrics")
        data = self._fetch_json(ro)
        if not data:
            return []
        items = data.get("data", {}).get("ownerMetric", [])
        return [parse_metrics(i) for i in items] if parse_metrics else items

    def retrieve_members(self) -> List[Any]:
        ro = self._make_request("members", description="load owner members")
        data = self._fetch_json(ro)
        if not data:
            return []
        items = data.get("data", {}).get("user", [])
        return [parse_member(i) for i in items] if parse_member else items

    def retrieve_mine(self) -> None:
        """Fetch owners for current user and add to this container (no api_response_handler)."""
        ro = self._make_request("mine", description="load owner mine")
        data = self._fetch_json(ro)
        if not data:
            return
        owners = data.get("data", {}).get("owner", [])
        if not isinstance(owners, list):
            owners = [owners]
        for item in owners:
            # turn dicts into attribute objects so Resource.add_obj() can index by .id/.name
            obj = types.SimpleNamespace(**item) if isinstance(item, dict) else item
            self.add_obj(obj)

class OwnerFilterObject(FilterObject):
    """Lightweight, read-only filter object for Owners."""

    def __init__(self, tc_obj):
        super().__init__(tc_obj)
        self._resource_properties = _OWNERS_PROPS

    @property
    def default_request_object(self) -> RequestObject:
        base = self._resource_properties["base"]
        ro = RequestObject()
        ro.set_description("filter by owner")
        ro.set_http_method("GET")
        ro.set_owner_allowed(base["owner_allowed"])
        ro.set_request_uri(base["uri"])
        ro.set_resource_pagination(base["pagination"])
        return ro
