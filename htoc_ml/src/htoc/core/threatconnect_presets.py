"""Shared ThreatConnect owner and indicator-type presets for production pipelines."""

INDICATOR_TYPES_WEEKLY = (
    "Address",
    "EmailAddress",
    "File",
    "Host",
    "URL",
    "ASN",
    "CIDR",
    "Email Subject",
    "Hashtag",
    "Mutex",
    "Registry Key",
    "User Agent",
    "Stripped URL",
)

INDICATOR_TYPES_DAILY = (
    "Address",
    "EmailAddress",
    "File",
    "Host",
    "URL",
    "ASN",
    "CIDR",
    "Email Subject",
    "Hashtag",
    "Mutex",
    "Registry Key",
    "User Agent",
)

# Weekly / ThreatScoreIW use the short Intel471 owner label in TC.
OWNERS_WEEKLY = (
    "HTOC Org",
    "CISA Federal Feed",
    "CMS_CTI",
    "Crowdstrike Falcon Intelligence",
    "DHS CISCP",
    "Intel471",
    "Mandiant Advantage Threat Intelligence",
    "VA_TIP Data",
)

# Daily PRISM adds Google TI and uses the long Intel 471 owner label in TC.
OWNERS_DAILY = (
    "HTOC Org",
    "CISA Federal Feed",
    "CMS_CTI",
    "Crowdstrike Falcon Intelligence",
    "DHS CISCP",
    "Intel 471 Intelligence",
    "Mandiant Advantage Threat Intelligence",
    "VA_TIP Data",
    "Google Threat Intelligence",
)
