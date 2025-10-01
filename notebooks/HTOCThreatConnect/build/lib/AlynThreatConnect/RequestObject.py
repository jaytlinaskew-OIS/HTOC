class RequestObject:
    """Minimal request object for ThreatConnect GET calls."""

    def __init__(self):
        # Core fields actually used by ThreatConnect.api_request
        self._headers = {}
        self._http_method = "GET"
        self._owner_allowed = True
        self._payload = {"createActivityLog": "false"}
        self._path_url = None
        self._request_uri = None
        self._stream = False
        self._body = None  # must exist; ThreatConnect reads ro.body

    # ---- Mutators ----

    def add_payload(self, key, val):
        """Add a key/value to the querystring payload."""
        self._payload[key] = "" if val is None else str(val)

    def empty_payload(self):
        self._payload = {}

    def add_header(self, key, val):
        """Add a key/value to headers."""
        self._headers[key] = "" if val is None else str(val)

    def enable_activity_log(self):
        """Enable TC activity log flag (safe no-op for your flow)."""
        self.add_payload("createActivityLog", "true")

    def set_http_method(self, data):
        """Set HTTP method (GET/POST/PUT/DELETE/OPTIONS)."""
        method = (data or "").upper()
        if method not in ["DELETE", "GET", "POST", "PUT", "OPTIONS"]:
            raise ValueError(f"Unsupported HTTP method: {data!r}")
        self._http_method = method
        # If you later use POST/PUT, ensure a content type:
        if method in ["POST", "PUT"] and "Content-Type" not in self._headers:
            self.add_header("Content-Type", "application/json")

    def set_owner_allowed(self, data):
        """Indicate if this request supports owners (called by caller)."""
        if isinstance(data, bool):
            self._owner_allowed = data

    def set_path_url(self, data):
        """Set path URL (included in HMAC signature)."""
        self._path_url = data

    def set_request_uri(self, uri_template, values=None):
        """Set the request URI (relative, e.g., '/v3/indicators?...')."""
        self._request_uri = uri_template if values is None else uri_template.format(*values)

    def set_stream(self, stream):
        if isinstance(stream, bool):
            self._stream = stream

    # Optional body setter (not used in GET, but harmless and future-proof)
    def set_body(self, data):
        """Set request body (mainly for POST/PUT)."""
        self._body = data
        # If you decide to set a body later, also set Content-Length conservatively:
        try:
            length = len(data) if data is not None else 0
        except TypeError:
            # Non-sized object; skip content-length
            length = None
        if length is not None:
            self.add_header("Content-Length", length)

    # ---- Properties ----

    @property
    def body(self):
        return self._body

    @property
    def headers(self):
        return self._headers

    @property
    def http_method(self):
        return self._http_method

    @property
    def owner_allowed(self):
        return self._owner_allowed

    @property
    def path_url(self):
        return self._path_url

    @property
    def payload(self):
        return self._payload

    @property
    def request_uri(self):
        return self._request_uri

    @property
    def stream(self):
        return self._stream

    # ---- Debug ----

    def __str__(self):
        printable = [
            "\n{:_^80}\n".format("Request Object"),
            "Request Settings",
            f"  Owner Allowed              {self.owner_allowed}",
            "",
            "HTTP Settings",
            f"  HTTP Method                {self.http_method}",
            f"  Request URI                {self.request_uri}",
            f"  Path URL                   {self.path_url}",
            f"  Body                       {type(self.body).__name__ if self.body is not None else 'None'}",
            "",
        ]
        if self.headers:
            printable.append("Headers")
            for k, v in self.headers.items():
                printable.append(f"  {k:<27}{v}")
            printable.append("")
        if self.payload:
            printable.append("Payload")
            for k, v in self.payload.items():
                printable.append(f"  {k:<27}{v}")
        return "\n".join(printable)
